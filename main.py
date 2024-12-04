import argparse
import copy
import os
import random
import json
import sys


def main():
    parser = argparse.ArgumentParser("")
    parser.add_argument("--config_path", type=str)
    args = parser.parse_args()
    config = json.load(open(args.config_path, "r"))

    trec_eval_path = config["trec_eval_path"]
    metric_name = config["metric_name"]
    base_dir = config["base_dir"]
    baseline_trecs = config["baseline_trecs"]
    new_model_trecs = config["new_model_trecs"]

    qrels = config["qrels"]
    markers = config["markers"]

    def get_mrr(trec_file, cutoff=10):
        k = cutoff

        qrel = {}
        with open(qrels, 'r') as f_qrel:
            for line in f_qrel:
                qid, _, did, label = line.strip().split()
                if qid not in qrel:
                    qrel[qid] = {}
                qrel[qid][did] = int(label)

        run = {}
        with open(trec_file, 'r') as f_run:
            for line in f_run:
                qid, _, did, _, _, _ = line.strip().split()
                if qid not in run:
                    run[qid] = []
                run[qid].append(did)

        mrr = 0.0
        intersect = 0
        results = {}
        for qid in run:
            rr = 0.0
            if qid in qrel:
                intersect += 1
                results[qid] = 0.0
                for i, did in enumerate(run[qid][:k]):
                    if did in qrel[qid] and qrel[qid][did] > 0:
                        rr = 1.0 / (i + 1)
                        results[qid] = rr
                        break
            mrr += rr
        mrr /= intersect
        results["all"] = mrr
        # print(len(set(results.keys())))
        return results

    def get_evaluation_per_query(trec_file):
        if metric_name.startswith("mrr_cut"):
            return get_mrr(trec_file, cutoff=int(metric_name.split(".")[1]))
        with os.popen(f"{trec_eval_path} -q -m {metric_name} {qrels} {trec_file}") as f:
            output = f.readlines()
        # print(output)
        results = {}
        for line in output:
            _, qid, metric = line.strip().split()
            results[qid] = float(metric)

        return results

    def randomization_test(evaluation_per_query_base, evaluation_per_query_target, total_test=1000):
        assert len(set(evaluation_per_query_base.keys())) == len(set(evaluation_per_query_target.keys())), (
        len(set(evaluation_per_query_base.keys())), len(set(evaluation_per_query_target.keys())))

        base_values, target_values = [], []
        for qid in evaluation_per_query_base.keys():
            if qid != "all":
                base_values.append(evaluation_per_query_base[qid])
                target_values.append(evaluation_per_query_target[qid])

        def random_swap(list_a, list_b):
            l_a = copy.deepcopy(list_a)
            l_b = copy.deepcopy(list_b)
            for i in range(len(list_a)):
                if random.random() > 0.5:
                    l_a[i], l_b[i] = l_b[i], l_a[i]
            return l_a, l_b

        diff = sum(target_values) / len(target_values) - sum(base_values) / len(base_values)
        cnt = 0
        for i in range(total_test):
            l_a, l_b = random_swap(base_values, target_values)
            cur_diff = sum(l_b) / len(l_b) - sum(l_a) / len(l_a)
            if cur_diff > diff:
                cnt += 1
        p = cnt / total_test
        return p

    baseline_evaluation_per_q, new_model_evaluation_per_q = {}, {}

    for trec in baseline_trecs:
        baseline_evaluation_per_q[trec] = get_evaluation_per_query(
            os.path.join(base_dir, trec) if not os.path.isabs(trec) else trec)
    for trec in new_model_trecs:
        new_model_evaluation_per_q[trec] = get_evaluation_per_query(os.path.join(base_dir, trec))
    # print(new_model_evaluation_per_q)

    sig_marks_baselines = [[] for _ in range(len(baseline_trecs))]
    for i in range(len(baseline_trecs)):
        for j in range(len(baseline_trecs)):
            if i != j:
                if baseline_evaluation_per_q[baseline_trecs[j]]["all"] > baseline_evaluation_per_q[baseline_trecs[i]]["all"]:
                    # print(baseline_trecs[i], baseline_trecs[j])
                    p_value = randomization_test(baseline_evaluation_per_q[baseline_trecs[i]],
                                                 baseline_evaluation_per_q[baseline_trecs[j]])
                    if p_value < 0.05:
                        sig_marks_baselines[j].append(i)

    sig_marks_new_model = [[] for _ in range(len(new_model_trecs))]
    for i in range(len(baseline_trecs)):
        for j in range(len(new_model_trecs)):
            p_value = randomization_test(baseline_evaluation_per_q[baseline_trecs[i]],
                                         new_model_evaluation_per_q[new_model_trecs[j]])
            # print(p_value)
            if p_value < 0.05:
                sig_marks_new_model[j].append(i)

    for i in range(len(baseline_trecs)):
        cur_markers = " ".join([markers[j] for j in sig_marks_baselines[i]])
        latex = "$\\text{}^{" + cur_markers + "}$"
        print(
            f"[{i}] {baseline_trecs[i]} \t {baseline_evaluation_per_q[baseline_trecs[i]]['all']} \t {sig_marks_baselines[i]} \t {latex}")
    for i in range(len(new_model_trecs)):
        cur_markers = " ".join([markers[j] for j in sig_marks_new_model[i]])
        latex = "$\\text{}^{" + cur_markers + "}$"
        print(
            f"[*] {new_model_trecs[i]} \t {new_model_evaluation_per_q[new_model_trecs[i]]['all']} \t {sig_marks_new_model[i]} \t {latex}")

    print('finish!')

if __name__ == '__main__':
    main()