# 2015 edition. Nathan Brixius
#

import csv
import scipy.stats as ss

def isnum(s):
    try:
        v = float(s)
        return 1
    except ValueError:
        return 0

def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)
        
def safediv(a, b, default):
    return a / b if abs(b) >= 1e16 else default

class football:
    # League rules. Change to suit.
    PtsTD=6.0
    PtsPassTD=6.0
    PtsInt=-2.0
    PtsFum=-2.0
    PassYdsPt=25.0
    RushYdsPt=10.0
    RecYdsPt=10.0
    PtsFG=3.0
    PtsFG40=4.0
    PtsFG50=5.0
    PtsFGMiss=-1.0
    PtsXPMiss=-1.0
    # Column names
    PASS_YDS = 'PassYds'
    RUSH_YDS = 'RushYds'
    REC_YDS = 'RecYds'
    RUSH_TD = 'RushTD'
    REC_TD = 'RecTD'
    # Other
    input_path = '//Users//nathanbrixius//SkyDrive//Public//NFL/2014//'
    calibrate = {}

    def readCsv(self, position):
	g=[]
	with open(self.input_path + position + '.csv', 'rU') as csvfile:
            r = csv.reader(csvfile)
	    headers = map((lambda x: x.strip().replace('/', '_').replace(' ', '_').replace('-', '_').replace('+', '_')), r.next())
	    for row in r:
	       g.append(dict(zip(headers, map((lambda x: num(x) if isnum(x) else x), row))))
	return g
	
    def writeCsv(self, data):
	with open(self.input_path + 'ratings.csv', 'wb') as csvfile:
            w = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            w.writerow(['Name', 'Position', 'RawPts', 'AdjPts', 'FPOR'])
            for player in data:
                w.writerow(player)

    def normalize(self, data, position, normalizeVar, obscount):
	minVal = sorted(data, key=(lambda x: -x[normalizeVar]))[obscount-1][normalizeVar]
	for player in data:
		player['Pos'] = position.upper()
		player['FFPtsN'] = player['FFPts'] - 1.0 * minVal 

    def recalibrate(self, data, obscount, calibrateVar):
        # find the highest scoring players.
	highestScoring = sorted(data, key=(lambda x: -x['FFPts0']))[:obscount-1]
	# fit a lognormal distribution to the calibarion variable for these players
	x = [player[calibrateVar] for player in highestScoring]
	(f0,f1,f2)= ss.lognorm.fit(x, floc=0)
        self.calibrate[position] = (f0, f1, f2)
	# use the distribution to produce a "corrected" verison of the calibration variable;
	# one that regresses to mean according to the distribution.
	for player in data:
		logNormCdf = ss.lognorm.cdf(player[calibrateVar], f0, f1, f2)
		player[calibrateVar + '_1'] = ss.lognorm.ppf(0.67 * logNormCdf + 0.33 * 0.5, f0, f1, f2)

    def scoreQB(self):
	data = self.readCsv('qb')
	for player in data:
		player['Att_Per_TD'] = safediv(player['Att'], player['TD'], 500)
		player['Rush_Per_TD'] = safediv(player['Rush'], player[self.RUSH_TD], 500)
		player['FFPts0'] = player['TD'] * self.PtsPassTD + player[self.RUSH_TD] * self.PtsTD + player['Int'] * self.PtsInt + player['FumL'] * self.PtsFum + player[self.PASS_YDS] / self.PassYdsPt + player[self.RUSH_YDS] / self.RushYdsPt
	self.recalibrate(data, 24, 'Rush_Per_TD')
	self.recalibrate(data, 24, 'Att_Per_TD')
	for player in data:
		player['TD_1'] = safediv(player['Att'], player['Att_Per_TD_1'], 0)
		player['Rush_TD_1'] = safediv(player['Rush'], player['Rush_Per_TD_1'], 0)
		player['FFPtsRaw'] = player['TD_1'] * self.PtsPassTD + player['Rush_TD_1'] * self.PtsTD + player['Int'] * self.PtsInt + player['FumL'] * self.PtsFum + player[self.PASS_YDS] / self.PassYdsPt + player[self.RUSH_YDS] / self.RushYdsPt
		player['FFPts'] = 15.0 * player['FFPtsRaw'] / player['G'] if player['G'] >= 10 else player['FFPtsRaw'] 
	self.normalize(data, 'qb', 'FFPts', 7)
	return data
	
    def scoreRB(self):
	data = self.readCsv('rb')
	for player in data:
		player['Rush_Per_TD'] = safediv(player['Rush'], player[self.RUSH_TD], 500)
		player['Rec_Per_TD'] = safediv(player['Rec'], player[self.REC_TD], 500)
		player['FFPts0'] = (player[self.REC_TD] + player[self.RUSH_TD]) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt + player[self.RUSH_YDS] / self.RushYdsPt
	self.recalibrate(data, 48, 'Rush_Per_TD')
	self.recalibrate(data, 48, 'Rec_Per_TD')
	for player in data:
		player['Rec_TD_1'] = safediv(player['Rec'], player['Rec_Per_TD_1'], 0)
		player['Rush_TD_1'] = safediv(player['Rush'], player['Rush_Per_TD_1'], 0)
		player['FFPtsRaw'] = (player['Rec_TD_1'] + player['Rush_TD_1']) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt + player[self.RUSH_YDS] / self.RushYdsPt
		player['FFPts'] = 15 * player['FFPtsRaw'] / player['G'] if player['G'] >= 10 else player['FFPtsRaw'] 
	self.normalize(data, 'rb', 'FFPts', 17)
	return data
	
    def scoreWR(self):
	data = self.readCsv('wr')
	for player in data:
		player['Rec_Per_TD'] = safediv(player['Rec'], player[self.REC_TD], 500)
		player['FFPts0'] = (player[self.REC_TD]) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt
	self.recalibrate(data, 48, 'Rec_Per_TD')
	for player in data:
		player['Rec_TD_1'] = safediv(player['Rec'], player['Rec_Per_TD_1'], 0)
		player['FFPtsRaw'] = (player['Rec_TD_1']) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt
		player['FFPts'] = 15 * player['FFPtsRaw'] / player['G'] if player['G'] >= 10 else player['FFPtsRaw'] 
	self.normalize(data, 'wr', 'FFPts', 17)
	return data

    def scoreTE(self):
	data = self.readCsv('te')
	for player in data:
		player['Rec_Per_TD'] = safediv(player['Rec'], player[self.REC_TD], 500)
		player['FFPts0'] = (player[self.REC_TD]) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt
	self.recalibrate(data, 24, 'Rec_Per_TD')
	for player in data:
		player['Rec_TD_1'] = safediv(player['Rec'], player['Rec_Per_TD_1'], 0)
		player['FFPtsRaw'] = (player['Rec_TD_1']) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt
		player['FFPts'] = 15 * player['FFPtsRaw'] / player['G'] if player['G'] >= 10 else player['FFPtsRaw'] 
	self.normalize(data, 'te', 'FFPts', 7)
	return data

    def scoreK(self):
	data = self.readCsv('k')
	for player in data:
		player['FFPts0'] = (player['M0_19'] + player['M20_29'] + player['M30_39']) * self.PtsFG + player['M40_49'] * self.PtsFG40 + player['M50_'] * self.PtsFG50 + player['XPM'] + (player['FGA'] - player['FGM']) * self.PtsFGMiss + (player['XPA'] - player['XPM']) * self.PtsXPMiss
		player['FFPts'] = player['FFPts0']
	self.normalize(data, 'k', 'FFPts', 7) # 12 team league
	return data

    def scoreDefST(self):
	defense = sorted(self.readCsv('def'), key=(lambda x: x['Team']))
	st = sorted(self.readCsv('st'), key=(lambda x: x['Team']))
	return zip(defense, st)
		
    def csvRow(self, p):
        return [p['Name'], p['Pos'], p['FFPts0'], p['FFPts'], p['FFPtsN']]

    def score(self):
        qb = self.scoreQB()
        rb = self.scoreRB()
        wr = self.scoreWR()
        te = self.scoreTE()
        k = self.scoreK()
        players = map(self.csvRow, qb) + map(self.csvRow, rb) + map(self.csvRow, wr) + map(self.csvRow, te) + map(self.csvRow, k)
        self.writeCsv(sorted(players, key=(lambda x: -x[len(x) - 1])))
        return players
        
