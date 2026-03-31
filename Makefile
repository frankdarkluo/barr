PYTHON ?= python
CONFIG ?= configs/week1_pilot.yaml

.PHONY: manifest smoke eval report week1

manifest:
	$(PYTHON) scripts/build_dataset_manifest.py --config $(CONFIG)

smoke: manifest
	$(PYTHON) scripts/run_inference.py --config $(CONFIG) --model-name dummy --quant-method bf16 --dataset-name mbbq --language english --backend dummy --limit 16
	$(PYTHON) scripts/parse_answers.py --config $(CONFIG) --inputs outputs/dummy/mbbq/english.jsonl
	$(PYTHON) scripts/eval_fairness.py --config $(CONFIG) --inputs outputs/dummy/mbbq/english.jsonl
	$(PYTHON) scripts/analyze_reasoning_dynamics.py --config $(CONFIG) --inputs outputs/dummy/mbbq/english.jsonl
	$(PYTHON) scripts/eval_counterfactual.py --config $(CONFIG) --inputs outputs/dummy/mbbq/english.jsonl
	$(PYTHON) scripts/summarize_week1.py --config $(CONFIG) --inputs outputs/dummy/mbbq/english.jsonl

eval:
	$(PYTHON) scripts/parse_answers.py --config $(CONFIG) --inputs $(INPUTS)
	$(PYTHON) scripts/eval_fairness.py --config $(CONFIG) --inputs $(INPUTS)
	$(PYTHON) scripts/analyze_reasoning_dynamics.py --config $(CONFIG) --inputs $(INPUTS)
	$(PYTHON) scripts/eval_counterfactual.py --config $(CONFIG) --inputs $(INPUTS)

report:
	$(PYTHON) scripts/summarize_week1.py --config $(CONFIG) --inputs $(INPUTS)

week1:
	@echo "1. make manifest"
	@echo "2. Run scripts/run_inference.py for each model / quant / dataset / language combination"
	@echo "3. make eval INPUTS='outputs/...jsonl outputs/...jsonl'"
	@echo "4. make report INPUTS='outputs/...jsonl outputs/...jsonl'"
