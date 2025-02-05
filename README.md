# ableton-repl

a simple remote REPL for Ableton's internal Python interpreter

- copy the AbletonREPL folder to `~/Music/Ableton/User Library/Remote Scripts`
- run Ableton
- in a terminal, run `nc localhost 13254`, you should be presented with a Python interpreter

you can call any Live Python API functions in this interpreter, which can be found [here](https://nsuspray.github.io/Live_API_Doc/11.0.0.xml)
