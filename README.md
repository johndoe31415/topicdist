# topicdist
When many students need to be divided up among (fewer) lecturers and each
student may give a ranking of preference, this tool generates a distribution
that takes into account both the student's wishes as well as the lecturers
preferences (e.g., maximum number of students to assign to this lecturer or
exclusion of a particular student because of a conflict of interest). The
results are scored and rerun until a good fit is found.

## Usage
There is, at minimum, one file needed: the preference file of the students.
From this it is inferred which topics (lecturers) are available and which
students are present. It is in CSV format and can be taken directly from
MOODLE. Input of multiple CSVs is possible. An example file is provided in
`example_preferences.csv`.

Additionally, one (or more) student JSON file(s) may be provided. This means
that even students will be included which did not submit any preference (and
thus won't appear in the CSV). An example of the format is shown in
`example_students.json`. Only the keys `vorname`, `nachname` and `email-dh` are
required per student.

Lastly, a lecuturer file can be provided to define conflicts of interest (a
particular lecturer wants to exclude students from being assigned to them) or a
maximum amount of students to take on. An example of this is shown in
`example_lecturers.json`.

With all the files present, simply:

```
$ ./topicdist -v -l example_lecturers.json -s example_students.json example_preferences.csv
Student assignments:
Angela Merkel <studi123@student.dhbw-mannheim.de>                      [2] Irgendwas mit Cyber
Ichhabdiedeadlineverpasst Ohnein <studi567@student.dhbw-mannheim.de>   [0] Irgendwas mit Medien
Jean-Baptiste Delacroix <studi456@student.dhbw-mannheim.de>            [3] Viertes Thema

Number of assignments per topic:
   Irgendwas mit Cyber (1)
        [2] Angela Merkel <studi123@student.dhbw-mannheim.de>
   Irgendwas mit Medien (1)
        [0] Ichhabdiedeadlineverpasst Ohnein <studi567@student.dhbw-mannheim.de>
   Viertes Thema (1)
        [3] Jean-Baptiste Delacroix <studi456@student.dhbw-mannheim.de>

Breakdown of preference matching:
   1 x 0
   1 x 2
   1 x 3

Total students: 3
Total score: 5
```

The optimization algorithm is quite stupid, it tries a randomized assignment
and compares scores. By default, 1000 iterations are run. The optimal score is
taken. It is output in the `assignments.json` file which can be used to send
emails: 

```json
{
	"assignments": [
		{
			"email": "studi123@student.dhbw-mannheim.de",
			"lecturer": null,
			"name": "Angela Merkel",
			"picked_pref": 2,
			"prefs": {
				"Irgendwas mit Cyber": 2,
				"Irgendwas mit Medien": 1,
				"Viertes Thema": 3
			},
			"topic": "Irgendwas mit Cyber"
		},
		{
			"email": "studi567@student.dhbw-mannheim.de",
			"lecturer": null,
			"name": "Ichhabdiedeadlineverpasst Ohnein",
			"picked_pref": 0,
			"prefs": {},
			"topic": "Irgendwas mit Medien"
		},
		{
			"email": "studi456@student.dhbw-mannheim.de",
			"lecturer": {
				"max_topics": 1
			},
			"name": "Jean-Baptiste Delacroix",
			"picked_pref": 3,
			"prefs": {
				"Irgendwas mit Cyber": 1,
				"Super duper Vorlesung": 2,
				"Viertes Thema": 3
			},
			"topic": "Viertes Thema"
		}
	],
	"meta": {
		"assigned_at_utc": "2024-01-09T12:49:33Z"
	}
}
```

## License
GNU GPL-3.
