# Statistical-significance

An open source library for conducting statistical-significance experiments.

## Getting Started

**1. Configure trec_eval environment**

  - Enter the trec_eval-master path and generate an executable trec_eval file
    ```
    cd trec_eval-master
    make
    ```
  - Modify "trec_eval_path" in config.json
      ```
        "trec_eval_path": "trec_eval-master/trec_eval",
      ```

**2. Data preparation**

Make sure that the .trec used is of the following format:

  ```
  {query_id} Q0 {document_id} {rank} {retrieval_score} {run_id}
  ```

**3. Edit config.json**

```
baseline_trecs: All baseline results. These results are tested for significance against each other
new_model_trecs: Your new model results. These results will not be tested for significance among each other, but will only be tested for significance with all baselines.
```

We provide an example. Please refer to the modification.😊

**4. Run**

```
  python main.py --config_path your config path
```
