gcloud compute ssh $* -- "tac udf.log | grep 'NEW STATEMENT' -B10000 -m1 | tac"
