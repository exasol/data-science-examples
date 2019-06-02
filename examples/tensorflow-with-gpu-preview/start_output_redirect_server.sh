gcloud compute ssh $* -- 'tmux new -d "python3 -m pyexasol script_debug --port 9999 &> udf.log"'
