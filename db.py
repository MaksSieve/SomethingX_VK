import json
import os.path

import pandas as pd


class User:

    def __init__(self):
        if os.path.isfile('users.csv'):
            self.df = pd.read_csv('users.csv')
            for user_id in self.df.user_id:
                self.set_auth(user_id=user_id, auth=0)
                self.set_context(user_id=user_id, context="")
        else:
            self.df = pd.DataFrame(columns=["user_id", "auth", "point", "context", "team"])

    def add_user(self, user_id):
        self.df = self.df.append({"user_id": user_id, "auth": int(0)}, ignore_index=True)

    def get_by_id(self, user_id):
        res = self.df[self.df.user_id == user_id]
        return json.loads(res.reset_index().to_json(orient='records'))[0] if not res.empty else None

    def set_auth(self, user_id, auth):
        self.df.loc[self.df.user_id == user_id, 'auth'] = int(auth)

    def set_context(self, user_id, context):
        self.df.loc[self.df.user_id == user_id, 'context'] = context

    def set_point(self, user_id, point):
        self.df.loc[self.df.user_id == user_id, 'point'] = point

    def get_context(self, user_id):
        return self.get_by_id(user_id)['context'] if self.get_by_id(user_id) else None

    def get_users(self):
        return json.loads(self.df.reset_index().to_json(orient='records')) if not self.df.empty else None

    def save(self):
        self.df.to_csv('users.csv')


class Team:

    def __init__(self):
        self.df = pd.read_json('teams.json')

    def get_team_by_id(self, team_id):
        res = self.df[self.df.team_id == team_id]
        return json.loads(res.reset_index().to_json(orient='records'))[0] if not res.empty else None

    def login(self, password, user_id, team_id):

        team = self.get_team_by_id(team_id=team_id)

        if team:
            if team['password'] == password:
                self.df.loc[self.df.team_id == team_id, 'user_id'] = user_id
                return True
            else:
                return False
        else:
            return False
