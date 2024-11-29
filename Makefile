SERVICES := app
DB_DATABASE:= template

help:
	@echo "Использование: make <command>"
	@echo "init                                 инициализация проекта"
	@echo "lint                                 запуск линтеров"
	@echo "bandit                               запуск поиска уязвимостей"
	@echo "test                                 запуск тестов"
	@echo "cover                                отчёт о покрытии тестами проекта"
	@echo "sort                                 сортировка импортов"
	@echo "migrations name=<название миграции>  создание миграции"
	@echo "migrate                              обновление бд миграциями"
	@echo "create_dump                          создание дампа данных бд"
	@echo "load_dump                            загрузка данных из дампа"

init:
	@poetry install
	@git-lfs install
	@git-lfs pull
	@pre-commit install

lint:
	@flake8 $(SERVICES)

bandit:
	@bandit -r "$(path)"

test:
	@pytest

cover:
	@coverage run --concurrency=thread,greenlet --source=$(SERVICES) -m pytest tests
	@coverage report

sort:
	@isort . -m 3 -e --fgw -q

migrations:
	@alembic revision --autogenerate -m "$(name)"

migrate:
	@alembic upgrade head

create_dump:
	@pg_dump --data-only -n public -T alembic_version -T spatial_ref_sys -T *_archive -h localhost -p 5432 -U postgres -d $(DB_DATABASE) -f db/$(SERVICES).data.sql

load_dump:
	@psql -h localhost -p 5432 -U postgres -d $(DB_DATABASE) -f db/$(SERVICES).data.sql
