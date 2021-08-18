# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 7-03-2021)
"""
	Fenomscrapers Project
"""

import re
try: #Py2
	from urlparse import parse_qs, urljoin
	from urllib import urlencode, quote_plus, unquote, unquote_plus
except ImportError: #Py3
	from urllib.parse import parse_qs, urljoin, urlencode, quote_plus, unquote, unquote_plus
from fenomscrapers.modules import cache
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 4
		self.language = ['en']
		self.domains = ['kick4ss.com', 'thekat.info', 'kickass.cm', 'kickass.ws', 'kickasst.net',
								'kickasshydra.dev', 'kickasshydra.net', 'kathydra.com', 'kickass.onl',
								'kickasstorrents.id', 'thekat.cc', 'kkat.net', 'kickasstorrents.bz']
		self._base_link = None
		self.moviesearch = '/usearch/{0}%20category:movies/?field=size&sorder=desc'
		self.tvsearch = '/usearch/{0}%20category:tv/?field=size&sorder=desc'
		self.min_seeders = 0
		self.pack_capable = True

	@property
	def base_link(self):
		if not self._base_link:
			self._base_link = cache.get(self.__get_base_url, 120, 'https://%s' % self.domains[0])
		return self._base_link

	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return

	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if not url: return
			url = parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urlencode(url)
			return url
		except:
			return

	def sources(self, url, hostDict):
		self.sources = []
		if not url: return self.sources
		try:
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			self.title = self.title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.episode_title = data['title'] if 'tvshowtitle' in data else None
			self.year = data['year']
			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else self.year

			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', query)
			urls = []
			if 'tvshowtitle' in data: url = self.tvsearch.format(quote_plus(query))
			else: url = self.moviesearch.format(quote_plus(query))
			url = urljoin(self.base_link, url)
			urls.append(url)

			if url.endswith('field=size&sorder=desc'):
				url2 = url.rsplit("/", 1)[0] + '/2/'
				urls.append(url2)
			else:
				url2 = url + '/2/'
				urls.append(url2)
			threads = []
			for url in urls:
				threads.append(workers.Thread(self.get_sources, url))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('KICKASS2')
			return self.sources

	def get_sources(self, url):
		# log_utils.log('url = %s' % url)
		try:
			headers = {'User-Agent': client.agent()}
			r = client.request(url, headers=headers, timeout='5')
			if not r: return
			posts = client.parseDOM(r, 'tr', attrs={'id': 'torrent_latest_torrents'})
		except:
			source_utils.scraper_error('KICKASS2')
			return
		for post in posts:
			try:
				ref = client.parseDOM(post, 'a', attrs={'title': 'Torrent magnet link'}, ret='href')[0]
				link = ref.split('url=')[1]

				url = unquote_plus(link).replace('&amp;', '&').replace(' ', '.').split('&tr')[0]
				if url in str(self.sources): continue
				hash = re.search(r'btih:(.*?)&', url, re.I).group(1)
				name = unquote_plus(url.split('&dn=')[1])
				name = source_utils.clean_name(name)

				if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year): continue
				name_info = source_utils.info_from_name(name, self.title, self.year, self.hdlr, self.episode_title)
				if source_utils.remove_lang(name_info): continue

				if not self.episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
					ep_strings = [r'[.-]s\d{2}e\d{2}([.-]?)', r'[.-]s\d{2}([.-]?)', r'[.-]season[.-]?\d{1,2}[.-]?']
					if any(re.search(item, name.lower()) for item in ep_strings): continue
				try:
					seeders = int(re.search(r'<td\s*class\s*=\s*["\']green\s*center["\']>([0-9]+|[0-9]+,[0-9]+)</td>', post, re.I).group(1).replace(',', ''))
					if self.min_seeders > seeders: continue
				except: seeders = 0

				quality, info = source_utils.get_release_quality(name_info, url)
				try:
					size = re.search(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', post).group(0)
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except: dsize = 0
				info = ' | '.join(info)
				self.sources.append({'provider': 'kickass2', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info,
												'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			except:
				source_utils.scraper_error('KICKASS2')

	def sources_packs(self, url, hostDict, search_series=False, total_seasons=None, bypass_filter=False):
		self.sources = []
		if not url: return self.sources
		try:
			self.search_series = search_series
			self.total_seasons = total_seasons
			self.bypass_filter = bypass_filter

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'].replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.imdb = data['imdb']
			self.year = data['year']
			self.season_x = data['season']
			self.season_xx = self.season_x.zfill(2)

			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', self.title)
			queries = [
						self.tvsearch.format(quote_plus(query + ' S%s' % self.season_xx)),
						self.tvsearch.format(quote_plus(query + ' Season %s' % self.season_x))]
			if self.search_series:
				queries = [
						self.tvsearch.format(quote_plus(query + ' Season')),
						self.tvsearch.format(quote_plus(query + ' Complete'))]
			threads = []
			for url in queries:
				link = urljoin(self.base_link, url)
				threads.append(workers.Thread(self.get_sources_packs, link))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('KICKASS2')
			return self.sources

	def get_sources_packs(self, link):
		# log_utils.log('link = %s' % link, __name__, log_utils.LOGDEBUG)
		try:
			headers = {'User-Agent': client.agent()}
			r = client.request(link, headers=headers, timeout='5')
			if not r: return
			posts = client.parseDOM(r, 'tr', attrs={'id': 'torrent_latest_torrents'})
		except:
			source_utils.scraper_error('KICKASS2')
			return
		for post in posts:
			try:
				ref = client.parseDOM(post, 'a', attrs={'title': 'Torrent magnet link'}, ret='href')[0]
				link = ref.split('url=')[1]
				url = unquote_plus(link).replace('&amp;', '&').replace(' ', '.').split('&tr')[0]
				hash = re.search(r'btih:(.*?)&', url, re.I).group(1)
				name = unquote_plus(url.split('&dn=')[1])
				name = source_utils.clean_name(name)

				if not self.search_series:
					if not self.bypass_filter:
						if not source_utils.filter_season_pack(self.title, self.aliases, self.year, self.season_x, name):
							continue
					package = 'season'

				elif self.search_series:
					if not self.bypass_filter:
						valid, last_season = source_utils.filter_show_pack(self.title, self.aliases, self.imdb, self.year, self.season_x, name, self.total_seasons)
						if not valid: continue
					else:
						last_season = self.total_seasons
					package = 'show'

				name_info = source_utils.info_from_name(name, self.title, self.year, season=self.season_x, pack=package)
				if source_utils.remove_lang(name_info): continue
				try:
					seeders = int(re.search(r'<td\s*class\s*=\s*["\']green\s*center["\']>([0-9]+|[0-9]+,[0-9]+)</td>', post, re.I).group(1).replace(',', ''))
					if self.min_seeders > seeders: continue
				except: seeders = 0

				quality, info = source_utils.get_release_quality(name_info, url)
				try:
					size = re.search(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', post).group(0)
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except: dsize = 0
				info = ' | '.join(info)
				item = {'provider': 'kickass2', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
							'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize, 'package': package}
				if self.search_series: item.update({'last_season': last_season})
				self.sources.append(item)
			except:
				source_utils.scraper_error('KICKASS2')

	def __get_base_url(self, fallback):
		for domain in self.domains:
			try:
				url = 'https://%s' % domain
				result = client.request(url, limit=1, timeout='5')
				try: result = re.search('r<title>(.+?)</title>', result, re.I).group(1)
				except: result = None
				if result and 'Kickass' in result: return url
			except:
				source_utils.scraper_error('KICKASS2')
		return fallback

	def resolve(self, url):
		return url