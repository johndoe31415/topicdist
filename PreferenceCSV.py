#	topicdist - Topic distribution among multiple lecturers
#	Copyright (C) 2023-2024 Johannes Bauer
#
#	This file is part of topicdist.
#
#	topicdist is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	topicdist is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with topicdist; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import csv
import json
import collections
import random

class PreferenceCSV():
	StudentEntry = collections.namedtuple("StudentEntry", [ "name", "email", "prefs" ])

	def __init__(self):
		self._students = { }
		self._topics = set()

	@property
	def student_count(self):
		return len(self._students)

	@property
	def topic_count(self):
		return len(self._topics)

	@property
	def students(self):
		return iter(self._students)

	@property
	def topics(self):
		return iter(self._topics)

	def get_student(self, student_email: str):
		return self._students[student_email]

	def get_students(self, student_emails: list[str]):
		return [ self.get_student(student_email) for student_email in student_emails ]

	def add_student(self, student_name: str, student_email: str, prefs: dict | None = None):
		if prefs is None:
			prefs = { }
		entry = self.StudentEntry(name = student_name, email = student_email, prefs = prefs)
		self._students[entry.email] = entry

	def add_topics(self, topics: list):
		self._topics |= set(topics)

	@classmethod
	def load_student_json_file(cls, filename: str):
		preference_csv = PreferenceCSV()
		with open(filename) as f:
			for student_data in json.load(f):
				student_name = f"{student_data['vorname']} {student_data['nachname']}"
				preference_csv.add_student(student_name, student_data["mail-dh"])
		return preference_csv

	@classmethod
	def load_from_file(cls, filename: str):
		preference_csv = PreferenceCSV()

		with open(filename, encoding = "utf-8-sig") as f:
			for (lineno, line) in enumerate(csv.reader(f), 1):
				if lineno == 1:
					topics = line[4:]
					preference_csv.add_topics(topics)
				else:
					student_name = line[0]
					student_email = line[2]
					student_prefs = line[4:]
					student_prefs = [ int(pref) for pref in student_prefs ]
					student_prefs = { topic: pref for (topic, pref) in zip(topics, student_prefs) }
					student_prefs = { topic: pref for (topic, pref) in student_prefs.items() if pref != 0 }
					preference_csv.add_student(student_name, student_email, student_prefs)
		return preference_csv

	def randomized_student_list(self):
		students = list(self._students.keys())
		random.shuffle(students)
		return students

	def randomized_topic_list(self):
		topics = list(self._topics)
		random.shuffle(topics)
		return topics

	def get_student_preference(self, student_email: str, preference_value: int):
		if student_email not in self._students:
			return None
		for (topic, pref_value) in self._students[student_email].prefs.items():
			if pref_value == preference_value:
				return topic
		return None

	def merge(self, preference_csv: "PreferenceCSV"):
		self._students.update(preference_csv._students)
		self._topics |= preference_csv._topics

	def __iter__(self):
		return iter(self._students.values())
