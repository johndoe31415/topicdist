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

import os
import sys
import math
import json
import functools
import datetime
import collections
from PreferenceCSV import PreferenceCSV
from PreferenceMatrix import PreferenceMatrix

class FinishedDistribution():
	def __init__(self, assignments_by_topic, prefs, lecturers):
		self._assignments_by_topic = assignments_by_topic
		self._prefs = prefs
		self._lecturers = lecturers

	@functools.cached_property
	def assignments_by_student(self):
		assignments = { }
		for (topic, assigned_emails) in self._assignments_by_topic.items():
			for email in assigned_emails:
				assignments[email] = topic
		return assignments

	@functools.cached_property
	def assignment_count(self):
		assignment_cnt = collections.Counter()
		for student in self._prefs:
			topic = self.assignments_by_student[student.email]
			pref = student.prefs.get(topic, 0)
			assignment_cnt[pref] += 1
		return assignment_cnt

	@functools.cached_property
	def score(self):
		score = 0
		for (pref, count) in self.assignment_count.items():
			score += pref * count
		return score

	def dump(self):
		print("Student assignments:")
		for student in sorted(self._prefs):
			topic = self.assignments_by_student[student.email]
			pref = student.prefs.get(topic, 0) if (len(student.prefs) > 0) else "-"

			name_email = f"{student.name} <{student.email}>"
			print(f"{name_email:<70s} [{pref}] {topic}")
		print()

		print("Number of assignments per topic:")
		for (topic, assigned_emails) in sorted(self._assignments_by_topic.items()):
			print(f"   {topic} ({len(assigned_emails)})")
			for student in sorted(self._prefs.get_students(assigned_emails)):
				name_email = f"{student.name} <{student.email}>"
				pref = student.prefs.get(topic, 0) if (len(student.prefs) > 0) else "-"
				print(f"        [{pref}] {name_email}")
		print()

		print("Breakdown of preference matching:")
		for (pref, count) in sorted(self.assignment_count.items()):
			print(f"   {count} x {pref}")
		print()
		print(f"Total students: {self._prefs.student_count}")
		print(f"Total score: {self.score}")

	def write(self, filename: str):
		json_object = {
			"meta": {
				"assigned_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
			},
			"assignments": [ ],
		}
		for student in sorted(self._prefs):
			topic = self.assignments_by_student[student.email]
			pref = student.prefs.get(topic, 0)
			json_object["assignments"].append({
				"name": student.name,
				"email": student.email,
				"topic": topic,
				"prefs": student.prefs,
				"picked_pref": pref,
				"lecturer": self._lecturers.get(topic),
			})

		with open(filename, "w") as f:
			json.dump(json_object, f, indent = "\t", sort_keys = True)

class TopicDistributor():
	def __init__(self, args):
		self._args = args
		self._prefs = self._load_pref_files()
		self._lecturers = self._load_lecturer_metadata()
		self._assignments_by_topic = None
		if self._args.verbose >= 2:
			print(f"{self._prefs.student_count} students and {self._prefs.topic_count} topics; default maximum of {self.default_max_assignments_per_lecturer} assignments per topic", file = sys.stderr)

	def _load_pref_files(self):
		prefs = PreferenceCSV()
		for filename in self._args.student_json:
			prefs.merge(PreferenceCSV.load_student_json_file(filename))
		for filename in self._args.preference_csv:
			prefs.merge(PreferenceCSV.load_from_file(filename))
		return prefs

	def _load_lecturer_metadata(self):
		if self._args.lecturer_json is None:
			return { }
		else:
			with open(self._args.lecturer_json) as f:
				return json.load(f)

	def assign(self, student_email: str, topic: str):
		self._assignments_by_topic[topic].append(student_email)
		self._unassigned_students.remove(student_email)
		self._topic_assignment_count[topic] = self._topic_assignment_count.get(topic, 0) + 1

	def assign_if_possible(self, student_email: str, topic: str):
		# How many students already have picked this topic?
		currently_picked = self._topic_assignment_count[topic]

		# How many does the lecturer want?
		max_topics_per_lecturer = self._max_assignments_for_topic(topic)

		if currently_picked >= max_topics_per_lecturer:
			# Lecturer already full, cannot assign.
			return False

		lecturer = self._lecturers.get(topic)
		if (lecturer is not None) and ("exclude" in lecturer):
			if student_email in lecturer["exclude"]:
				# Lecturer has a conflict of interest with this student, do not consider.
				return False

		self.assign(student_email, topic)
		return True

	@functools.cached_property
	def	default_max_assignments_per_lecturer(self):
		remaining_lecturers = self._prefs.topic_count
		remaining_students = self._prefs.student_count
		for lecturer in self._lecturers.values():
			if "max_topics" in lecturer:
				remaining_lecturers -= 1
				remaining_students -= lecturer["max_topics"]
		assert(remaining_lecturers > 0)
		return math.ceil(remaining_students / remaining_lecturers)

	def _max_assignments_for_topic(self, topic):
		if (topic in self._lecturers) and ("max_topics" in self._lecturers[topic]):
			return self._lecturers[topic]["max_topics"]
		else:
			return self.default_max_assignments_per_lecturer

	def _build_lecture_list(self):
		lecture_list = [ ]
		remaining_lecturers = self._prefs.topic_count
		remaining_students = self._prefs.student_count

		# Fixed assignments first
		for (topic, lecturer) in self._lecturers.items():
			if "max_topics" in lecturer:
				remaining_lecturers -= 1
				remaining_students -= lecturer["max_topics"]
				lecture_list += [ topic ] * lecturer["max_topics"]

		# Variable assignments thereafter, choose Bresenham-type interpolation
		# (fractional topics_per_lecturer)
		topics_per_lecturer = remaining_students / remaining_lecturers
		for topic in self._prefs.randomized_topic_list():
			lecturer = self._lecturers.get(topic, { })
			if "max_topics" not in lecturer:
				assign_count = round(remaining_students) - round(remaining_students - topics_per_lecturer)
				remaining_students -= topics_per_lecturer
				lecture_list += [ topic ] * assign_count

		return lecture_list

	def _build_student_lecture_matrix(self):
		student_list = self._prefs.randomized_student_list()
		lecture_list = self._build_lecture_list()
		pmatrix = PreferenceMatrix(student_list, lecture_list)
		for student in self._prefs:
			for (topic, pref) in student.prefs.items():
				pmatrix.set_preference(student.email, topic, pref)

		for (topic, lecturer) in self._lecturers.items():
			if "exclude" in lecturer:
				for exclusion_student_email in lecturer["exclude"]:
					pmatrix.set_preference(exclusion_student_email, topic, -99999999)
		return pmatrix

	def run(self):
		self._assignments_by_topic = collections.defaultdict(list)
		self._unassigned_students = set(student_email for student_email in self._prefs.students)
		self._topic_assignment_count = collections.Counter({ topic: 0 for topic in self._prefs.topics })

		pmatrix = self._build_student_lecture_matrix()
		assignments_by_topic = pmatrix.assign()
		return FinishedDistribution(assignments_by_topic, self._prefs, self._lecturers)
