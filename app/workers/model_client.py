import asyncio
import json
import logging
import ipaddress

import joblib
from redis.asyncio.client import Redis

import pandas as pd

from app.config import settings, get_logger


class ModelClient:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.logger = get_logger(__name__)
        self.model = joblib.load("config/gradient_boosting_model-0,9899.pkl")
        self.logger.info("Модель загружена успешно!")

    async def inference(self, data):
        try:
            df = pd.DataFrame([data])

            df_preprocessed = self._preprocessing(df)
            result = self._processing(df_preprocessed)
            data = self._postprocessing(data, result)
            await self._send_to_queue(data)
            await asyncio.sleep(10)
        except Exception as e:
            self.logger.exception(f"Ошибка работы инференса --- {e}")
        else:
            self.logger.info(f"Инференс отработал успешно! --- {data['id']}")

    def _preprocessing(self, df: pd.DataFrame) -> pd.DataFrame:
        columns = [
            "ip",
            "device_id",
            "tran_code",
            "mcc",
            "client_id",
            "pin_inc_count",
            "expiration_date",
            "datetime",
            "sum",
            "balance",
            "device_type_ATM",
            "device_type_Portable term",
            "device_type_atm",
            "device_type_cash_in",
            "device_type_cash_out",
            "device_type_port_trm",
            "device_type_pos trm",
            "device_type_prtbl trm",
            "oper_type_add_on_acc",
            "oper_type_bad",
            "oper_type_blk",
            "oper_type_blocked",
            "oper_type_country_transfer",
            "oper_type_decrease_on_acc",
            "oper_type_diff_cntry",
            "oper_type_err",
            "oper_type_err_code",
            "oper_type_from_acc",
            "oper_type_in",
            "oper_type_in_acc",
            "oper_type_out",
            "oper_type_payment",
            "oper_type_transfer",
            "card_status_act",
            "card_status_active",
            "card_status_blk",
            "card_status_blocked",
            "card_type_CREDIT",
            "card_type_DEBIT",
        ]
        df_combined = df.drop(columns=["transaction_id"])
        df_combined = df_combined.drop(columns=["id"])
        df_combined = pd.get_dummies(df_combined, columns=["device_type"])
        df_combined[df_combined.columns[df_combined.columns.str.startswith("device_type")]] = df_combined[
            df_combined.columns[df_combined.columns.str.startswith("device_type")]
        ].astype(int)
        df_combined = pd.get_dummies(df_combined, columns=["oper_type"])
        df_combined[df_combined.columns[df_combined.columns.str.startswith("oper_type")]] = df_combined[
            df_combined.columns[df_combined.columns.str.startswith("oper_type")]
        ].astype(int)
        df_combined = pd.get_dummies(df_combined, columns=["card_status"])
        df_combined[df_combined.columns[df_combined.columns.str.startswith("card_status")]] = df_combined[
            df_combined.columns[df_combined.columns.str.startswith("card_status")]
        ].astype(int)
        df_combined = pd.get_dummies(df_combined, columns=["card_type"])
        df_combined[df_combined.columns[df_combined.columns.str.startswith("card_type")]] = df_combined[
            df_combined.columns[df_combined.columns.str.startswith("card_type")]
        ].astype(int)
        df_combined["ip"] = df_combined["ip"].apply(lambda x: int(ipaddress.IPv4Address(x)))
        df_combined["datetime"] = pd.to_datetime(df_combined["datetime"])
        df_combined["datetime"] = df_combined["datetime"].apply(lambda x: x.timestamp())
        df_combined["expiration_date"] = pd.to_datetime(df_combined["expiration_date"])
        df_combined["expiration_date"] = df_combined["expiration_date"].apply(lambda x: x.timestamp())
        for col in columns:
            if col not in df_combined.columns:
                df_combined[col] = 0
        df_combined = df_combined[columns]
        return df_combined

    def _processing(self, df: pd.DataFrame) -> float:
        predictions = self.model.predict_proba(df)
        return float(predictions[:, 1][0])

    def _postprocessing(self, data: dict, result: float) -> dict:
        data["pred"] = result
        return data

    async def _send_to_queue(self, data: dict):
        data_json = json.dumps(data)

        await self.redis.rpush(settings.AMQP.routing_keys.backend_routing_key, data_json)
