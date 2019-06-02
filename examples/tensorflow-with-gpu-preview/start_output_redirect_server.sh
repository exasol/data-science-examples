old_pid=$(ps --no-headers -exo "uname:1,pid:1,args:1" | grep "[t]mux new -d python3 -m pyexasol" | cut -f 2 -d " ")
if [ -z "$old_pid" ]
then
  tmux new -d "python3 -m pyexasol script_debug --port 9999 &> udf.log"
fi
