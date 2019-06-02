old_pid=$(ps --no-headers -exo "uname:1,pid:1,args:1" | grep "tmux new -d python3 -m pyexasol" | grep root | cut -f 2 -d " ")
if [ -z "$old_pid" ]
then
  gcloud compute ssh $* -- 'tmux new -d "python3 -m pyexasol script_debug --port 9999 &> udf.log"'
fi
