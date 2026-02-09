find . -type f -name "*.qmd" -exec perl -i -pe '
  if (/{python}/) {
    s/{python}/{pyodide}/g;
  }
' {} +

find . -type f -name "*.qmd" -exec perl -i -0777 -pe '
  s/(\{pyodide\})(?!\n#\| caption)/$1\n#| caption: "▶ Ctrl\/Cmd+Enter | ⇥ Ctrl\/Cmd+] | ⇤ Ctrl\/Cmd+\["/g;
' {} +


# turn this on to collapse to one line if there is a mistake

find . -type f -name "*.qmd" -exec perl -i -0777 -pe '
  s/(#\| caption: "▶ Ctrl\/Cmd\+Enter \| ⇥ Ctrl\/Cmd\+\] \| ⇤ Ctrl\/Cmd\+\[")[\s\S]*?(?=\n(?!#\| caption)|\Z)/$1/mg;
' {} +