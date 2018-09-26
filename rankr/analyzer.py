import operator
import numpy as np
import rankr.constants as constants

from datetime import datetime
from dateutil import rrule
from rankr.fetchers.rankings_fetcher import RankingsFetcher
from rankr.fetchers.leaders_fetcher import LeadersFetcher


class Analyzer():
	def __init__(self, league_id):
		self._league_id = league_id
		self._rf = RankingsFetcher(self._league_id)
		self._lf = LeadersFetcher(self._league_id)
		self._latest_week = self._find_latest_week()

	def get_weekly_ranking_errors(self, week):
		if not self._is_valid_week(week):
			raise ValueError("Invalid Week Provided")

		data = self._rf.fetch_rankings_by_week(week)
		weekly_errors = {}

		for position in constants.POSITIONS:
			errors = {}
			leaders = self._lf.fetch_weekly_leaders(week, position)
			# Use root mean squared error as the error estimate
			for analyst in constants.ANALYSTS:
				total_error = 0

				position_ranks = data.get_position_rankings_by_analyst(position, analyst)
				for rank in range(len(leaders)):
					player = leaders[rank]
					predicted_rank = position_ranks.loc[position_ranks['PLAYER'] == player]
					try:
						analyst_rank = predicted_rank.iloc[0][analyst]
						total_error += ((analyst_rank - rank) ** 2)
					except IndexError:
						max_rank = constants.MAX_RANKS[position]
						total_error += ((max_rank - rank) ** 2)
				rmse = np.sqrt(total_error / len(leaders))
				errors[analyst] = rmse

			weekly_errors[position] = self._get_nrmsd(errors)

		return weekly_errors

	# Calculate normalized root mean square deviation
	# https://en.wikipedia.org/wiki/Root-mean-square_deviation#Normalized_root-mean-square_deviation
	def _get_nrmsd(self, analyst_errors):
		mean = np.mean(list(analyst_errors.values()))
		nrmsd_errors = { k: v / mean for k, v in analyst_errors.items() }
		return nrmsd_errors

	def _is_valid_week(self, week):
		try:
			week_val = int(week)
			return week_val > 0 and week_val <= self._latest_week
		except ValueError:
			return False

	def _find_latest_week(self):
		start_date = datetime.strptime(constants.SEASON_START, "%b %d %Y")
		weeks = rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=datetime.now())
		num_weeks = weeks.count()
		return num_weeks

	def _is_valid_position(self, position):
		try:
			position_val = int(position)
			return position_val in constants.POSITIONS
		except ValueError:
			return False
