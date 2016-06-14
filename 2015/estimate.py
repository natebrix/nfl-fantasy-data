# 2016 edition. Nathan Brixius
#

import csv
import scipy.stats as ss
import pandas as pd
import numpy as np

def safediv(a, b, default):
    return (a / b).replace(np.inf, default).fillna(default)

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
    input_path = r'C:\\Users\\Nathan\\OneDrive\\Public\\NFL\\2015\\'
    calibrate = {}

    def normalize(self, data, position, normalizeVar, obscount):
        minVal = data.sort_values(by=normalizeVar, ascending=False).iloc[obscount-1][normalizeVar]
        data['Pos'] = position.upper()
        data['FFPtsN'] = data['FFPts'] - 1.0 * minVal

    def recalibrate(self, data, obscount, calibrateVar):
        # find the highest scoring players.
        highestScoring = data.sort_values(by='FFPts0', ascending=False)[:obscount-1]
        # fit a lognormal distribution to the calibarion variable for these players
        (f0,f1,f2) = ss.lognorm.fit(highestScoring[calibrateVar], floc=0)
        # use the distribution to produce a "corrected" verison of the calibration variable;
        # one that regresses to mean according to the distribution.
        logNormCdf = ss.lognorm.cdf(data[calibrateVar], f0, f1, f2)
        data[calibrateVar + '_1'] = ss.lognorm.ppf(0.67 * logNormCdf + 0.33 * 0.5, f0, f1, f2)

    def score_QB(self):
        player = pd.read_csv(self.input_path + 'qb.csv')
        player['Att_Per_TD'] = safediv(player['Att'], player['TD'], 500)
        player['Rush_Per_TD'] = safediv(player['Rush'], player[self.RUSH_TD], 500)
        player['FFPts0'] = player['TD'] * self.PtsPassTD + player[self.RUSH_TD] * self.PtsTD + player['Int'] * self.PtsInt + player['FumL'] * self.PtsFum + player[self.PASS_YDS] / self.PassYdsPt + player[self.RUSH_YDS] / self.RushYdsPt
        self.recalibrate(player, 24, 'Rush_Per_TD')
        self.recalibrate(player, 24, 'Att_Per_TD')
        player['TD_1'] = safediv(player['Att'], player['Att_Per_TD_1'], 0)
        player['Rush_TD_1'] = safediv(player['Rush'], player['Rush_Per_TD_1'], 0)
        player['FFPtsRaw'] = player['TD_1'] * self.PtsPassTD + player['Rush_TD_1'] * self.PtsTD + player['Int'] * self.PtsInt + player['FumL'] * self.PtsFum + player[self.PASS_YDS] / self.PassYdsPt + player[self.RUSH_YDS] / self.RushYdsPt
        #player['FFPts'] = 15.0 * player['FFPtsRaw'] / player['G'] if player['G'] >= 10 else player['FFPtsRaw']
        player['FFPts'] = player.apply(lambda p: 15.0 * p['FFPtsRaw'] / p['G'] if p['G'] >= 10 else p['FFPtsRaw'], axis=1)
        self.normalize(player, 'qb', 'FFPts', 7)
        return player

    def score_RB(self):
        player = pd.read_csv(self.input_path + 'rb.csv')
        player['Rush_Per_TD'] = safediv(player['Rush'], player[self.RUSH_TD], 500)
        player['Rec_Per_TD'] = safediv(player['Rec'], player[self.REC_TD], 500)
        player['FFPts0'] = (player[self.REC_TD] + player[self.RUSH_TD]) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt + player[self.RUSH_YDS] / self.RushYdsPt
        self.recalibrate(player, 48, 'Rush_Per_TD')
        self.recalibrate(player, 48, 'Rec_Per_TD')
        player['Rec_TD_1'] = safediv(player['Rec'], player['Rec_Per_TD_1'], 0)
        player['Rush_TD_1'] = safediv(player['Rush'], player['Rush_Per_TD_1'], 0)
        player['FFPtsRaw'] = (player['Rec_TD_1'] + player['Rush_TD_1']) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt + player[self.RUSH_YDS] / self.RushYdsPt
        player['FFPts'] = player.apply(lambda p: 15 * p['FFPtsRaw'] / p['G'] if p['G'] >= 10 else p['FFPtsRaw'], axis=1)
        self.normalize(player, 'rb', 'FFPts', 17)
        return player

    def score_WR(self):
        player = pd.read_csv(self.input_path + 'wr.csv')
        player['Rec_Per_TD'] = safediv(player['Rec'], player[self.REC_TD], 500)
        player['FFPts0'] = (player[self.REC_TD]) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt
        self.recalibrate(player, 48, 'Rec_Per_TD')
        player['Rec_TD_1'] = safediv(player['Rec'], player['Rec_Per_TD_1'], 0)
        player['FFPtsRaw'] = (player['Rec_TD_1']) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt
        player['FFPts'] = player.apply(lambda p: 15 * p['FFPtsRaw'] / p['G'] if p['G'] >= 10 else p['FFPtsRaw'], axis=1)
        self.normalize(player, 'wr', 'FFPts', 17)
        return player

    def score_TE(self):
        player = pd.read_csv(self.input_path + 'te.csv')
        player['Rec_Per_TD'] = safediv(player['Rec'], player[self.REC_TD], 500)
        player['FFPts0'] = (player[self.REC_TD]) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt
        self.recalibrate(player, 24, 'Rec_Per_TD')
        player['Rec_TD_1'] = safediv(player['Rec'], player['Rec_Per_TD_1'], 0)
        player['FFPtsRaw'] = (player['Rec_TD_1']) * self.PtsTD + player['FumL'] * self.PtsFum + player[self.REC_YDS] / self.RecYdsPt
        player['FFPts'] = player.apply(lambda p: 15 * p['FFPtsRaw'] / p['G'] if p['G'] >= 10 else p['FFPtsRaw'], axis=1)
        self.normalize(player, 'te', 'FFPts', 7)
        return player

    def score_K(self):
        player = pd.read_csv(self.input_path + 'k.csv')
        player['FFPts0'] = (player['M0-19'] + player['M20-29'] + player['M30-39']) * self.PtsFG + player['M40-49'] * self.PtsFG40 + player['M50+'] * self.PtsFG50 + player['XPM'] + (player['FGA'] - player['FGM']) * self.PtsFGMiss + (player['XPA'] - player['XPM']) * self.PtsXPMiss
        player['FFPts'] = player['FFPts0']
        self.normalize(player, 'k', 'FFPts', 7) # 12 team league
        return player

    def score_DefST(self):
        defense = pd.read_csv(self.input_path + 'def.csv')
        #defense = sorted(self.readCsv('def'), key=(lambda x: x['Team']))
        #st = sorted(self.readCsv('st'), key=(lambda x: x['Team']))
        st = pd.read_csv(self.input_path + 'st.csv')
        return zip(defense, st) # todo merge on Team
		
    def score(self):
        qb = self.score_QB()
        rb = self.score_RB()
        wr = self.score_WR()
        te = self.score_TE()
        k = self.score_K()
        players = pd.concat([qb, rb, wr, te, k], join='inner')
        return players.sort_values(by='FFPtsN', ascending=False)
