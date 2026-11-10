PERSONAL FITNESS TRACKER - WEEK 3

Run with: python personal_fitness_tracker.py

The config folder MUST stay alongside the Python file and contain:
  workout_list.json - user-maintained selectable workout catalog
  fitness_tools.json - command descriptions
  instruction.txt - application guide


The records directory is created automatically and stores <Name>_wk_Coll.json.
The genrpt command writes <Name>_wk_report.txt to the application root.

Main menu: 1 Load Collection, 2 Enter New Collection.
New: daily calorie goal -> name -> choose workout indexes -> done -> log results.
Load: choose saved collection -> daily calorie goal -> re-enter workout results.
Commands before completion: Help, Instr, Home, Exit.
After completion, the header also shows Tools: anawk, summary, genrpt.
Both duration and calorie prompts identify the selected workout by name.

