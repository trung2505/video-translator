ALEMBIC=alembic

.PHONY: migrate revision upgrade downgrade

migrate:
	@${ALEMBIC} revision --autogenerate -m "autogen"

revision:
	@${ALEMBIC} revision -m "$(MESSAGE)"

upgrade:
	@${ALEMBIC} upgrade head

downgrade:
	@${ALEMBIC} downgrade -1
