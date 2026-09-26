.PHONY: help install unleash seed traffic scan mcp serve demo-reset audit agent clean

help:
	@echo "Feature Flag Reaper — demo targets"
	@echo "  make install      install python deps"
	@echo "  make unleash      start Unleash + Postgres (docker)"
	@echo "  make seed         seed the 8-flag demo matrix (idempotent)"
	@echo "  make traffic      start the live traffic simulator (background)"
	@echo "  make scan         run the reaper scan and print verdicts"
	@echo "  make mcp          start the MCP tool server (port 8900)"
	@echo "  make serve        alias of mcp (report/audit views included)"
	@echo "  make demo-reset   full reset for repeatable demos"
	@echo "  make audit        print the audit trail"

install:
	pip install -r requirements.txt

unleash:
	docker compose -f docker-compose.unleash.yml up -d
	@python3 scripts/wait_unleash.py

seed:
	python3 scripts/seed_unleash.py

traffic:
	python3 -u scripts/simulate_traffic.py &

scan:
	python3 -m reaper.scan --min-age-hours 0

mcp serve:
	python3 -m reaper.server

demo-reset:
	pkill -f simulate_traffic 2>/dev/null; true
	docker compose -f docker-compose.unleash.yml down -v
	docker compose -f docker-compose.unleash.yml up -d
	@python3 scripts/wait_unleash.py
	python3 scripts/seed_unleash.py
	rm -f audit/unleash_client_token
	python3 scripts/seed_unleash.py > /dev/null
	cd demo/checkout-service && git checkout -- . && git clean -fdq
	-python3 -c "import pathlib,shutil; shutil.rmtree(pathlib.Path('/tmp/reaper-work'), ignore_errors=True)"
	rm -f audit/state.json
	python3 -c "from reaper import audit; audit.reset()"
	@echo "demo reset (volume wiped — metrics history is truly zero). Start traffic with: make traffic"

audit:
	@python3 -c "from reaper import audit; [print(e['ts'], e['actor'], e['action']) for e in audit.tail(50)]"

agent:
	python3 scripts/setup_agent.py

clean:
	rm -rf /tmp/reaper-work /tmp/reaper-e2e
