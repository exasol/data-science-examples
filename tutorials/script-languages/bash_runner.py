from pexpect import replwrap, EOF
import pexpect
# Inspired by https://github.com/takluyver/bash_kernel
class IREPLWrapper(replwrap.REPLWrapper):
    """A subclass of REPLWrapper that gives incremental output
    The parameters are the same as for REPLWrapper, except for one
    extra parameter:
    :param line_output_callback: a callback method to receive each batch
      of incremental output. It takes one string parameter.
    """
    def __init__(self, cmd_or_spawn, orig_prompt, prompt_change,
                 extra_init_cmd=None, line_output_callback=None):
        self.line_output_callback = line_output_callback
        replwrap.REPLWrapper.__init__(self, cmd_or_spawn, orig_prompt,
                                      prompt_change, extra_init_cmd=extra_init_cmd)

    def _expect_prompt(self, timeout=-1):
        if timeout == None:
            # "None" means we are executing code from a Jupyter cell by way of the run_command
            # in the do_execute() code below, so do incremental output.
            while True:
                pos = self.child.expect_exact([self.prompt, self.continuation_prompt, u'\r\n'],
                                              timeout=None)
                if pos == 2:
                    # End of line received
                    self.line_output_callback(self.child.before)
                else:
                    if len(self.child.before) != 0:
                        # prompt received, but partial line precedes it
                        self.line_output_callback(self.child.before)
                    break
        else:
            # Otherwise, use existing non-incremental code
            pos = replwrap.REPLWrapper._expect_prompt(self, timeout=timeout)

        # Prompt received, so return normally
        return pos

def run(code):
    child = pexpect.spawn("bash", echo=False, encoding='utf-8', codec_errors='replace')
    ps1 = replwrap.PEXPECT_PROMPT[:5] + u'\[\]' + replwrap.PEXPECT_PROMPT[5:]
    ps2 = replwrap.PEXPECT_CONTINUATION_PROMPT[:5] + u'\[\]' + replwrap.PEXPECT_CONTINUATION_PROMPT[5:]
    prompt_change = u"PS1='{0}' PS2='{1}' PROMPT_COMMAND=''".format(ps1, ps2)

    # Using IREPLWrapper to get incremental output
    bashwrapper = IREPLWrapper(child, u'\$', prompt_change,
                                    extra_init_cmd="export PAGER=cat",
                                    line_output_callback=lambda x: print(x))
    bashwrapper.run_command(code.rstrip(), timeout=None)
