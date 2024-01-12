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

import collections
import scipy.optimize

class PreferenceMatrix():
	def __init__(self, student_list, lecture_list):
		self._student_list = student_list
		self._lecture_list = lecture_list
		self._sparse = { }
		assert(len(self._student_list) == len(self._lecture_list))

	@property
	def size(self):
		return len(self._student_list)

	def set_preference(self, student, lecture, score):
		self._sparse[(student, lecture)] = score

	@property
	def M(self):
		M = [ ]
		for student in self._student_list:
			row = [ ]
			for lecture in self._lecture_list:
				row.append(self._sparse.get((student, lecture), 0))
			M.append(row)
		return M

	def assign(self):
		assignments_by_topic = collections.defaultdict(list)
		(row_indices, col_indices) = scipy.optimize.linear_sum_assignment(self.M, maximize = True)
		for (row_index, col_index) in zip(row_indices, col_indices):
			student_email = self._student_list[row_index]
			lecture_topic = self._lecture_list[col_index]
			assignments_by_topic[lecture_topic].append(student_email)
		return assignments_by_topic
