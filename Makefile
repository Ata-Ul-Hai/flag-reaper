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

demo-reset: unleash
	pkill -f simulate_traffic 2>/dev/null; true
	python3 scripts/seed_unleash.py
	cd demo/checkout-service && git checkout -- . && git clean -fdq
	-python3 -c "import pathlib,shutil; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path('/tmp/reaper-work')]]"
	python3 -c "from reaper import audit; audit.reset()"
	@echo "demo reset. Start traffic with: make traffic   (background), then: make scan"

audit:
	@python3 -c "from reaper import audit; [print(e['ts'], e['actor'], e['action']) for e in audit.tail(50)]"

agent:
	python3 scripts/setup_agent.py

clean:
	rm -rf /tmp/reaper-work /tmp/reaper-e2e
