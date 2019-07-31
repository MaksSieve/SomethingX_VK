from datetime import datetime


class Resource:

    def __init__(self, name: str, k: int, min_price: int, production: int, max_price: int):
        self.max_price = max_price
        self.name = name
        self.k = k
        self.min_price = min_price
        self.production = production


class Point:
    def __init__(self, name: str, base_resource: int, storage: list):
        self.name = name
        self.base_resource = base_resource
        self.storage = storage


class Game:

    def __init__(self, game_config):
        self.state = 0
        self.name = game_config['name'].encode('utf-8').decode()
        self.game_time = game_config['game_time']
        self.period = game_config['period']
        self.gov_pass = game_config['gov_pass']
        self.adm_pass = game_config['adm_pass']
        self.help_message = game_config['help_message']
        self.resources = [Resource(
            name=resource['name'],
            k=resource["k"],
            production=resource["production"],
            min_price=resource["min_price"],
            max_price=resource["max_price"])
            for resource in game_config['resources']]
        self.points = [Point(
            name=point['name'],
            base_resource=point["base_resource"],
            storage=[res for res in point["resources"]])
            for point in game_config['points']]
        self.news = []

    def start(self):
        self.state = 1
        self.start_time = datetime.now()

    def stop(self):
        self.state = 0

    def get_points_names(self):
        return [point.name for point in self.points]

    def get_point_by_name(self, name):
        return next(filter(lambda point: point.name.upper() == name, self.points), None)

    def get_resource_price(self, name, point):
        resource_id = self.resources.index(
            next(filter(lambda resource: resource.name.upper() == name, self.resources), None))
        point = self.get_point_by_name(point)
        return point.storage[resource_id]['price']

    def is_base_resource(self, name, point):
        point = self.get_point_by_name(point)
        return self.resources[point.base_resource].name.upper() == name.upper()

    def check_availability(self, name, point, amount):
        point = self.get_point_by_name(point)
        resource_id = self.resources.index(
            next(filter(lambda resource: resource.name.upper() == name, self.resources), None))
        return point.storage[resource_id]['amount'] >= amount

    def get_resources_on_point_string(self, point_name):
        resources = self.get_point_by_name(point_name).storage
        msg = "name - amount - price\n"
        for res in resources:
            res_id = resources.index(res)
            msg = msg + f"{self.resources[res_id].name} - " \
                        f"{res['amount']} - " \
                        f"{res['price']}\n"
        return msg

    def buy(self, point, name, amount):
        point = self.get_point_by_name(point)
        resource_id = self.resources.index(
            next(filter(lambda resource: resource.name.upper() == name, self.resources), None))

        point.storage[resource_id]['amount'] += amount

    def sell(self, point, name, amount):
        point = self.get_point_by_name(point)
        resource_id = self.resources.index(
            next(filter(lambda resource: resource.name.upper() == name, self.resources), None))
        point.storage[resource_id]['amount'] -= amount

    def update_prices(self):
        for point in self.points:
            for resource in point.storage:
                res = self.resources[point.storage.index(resource)]
                resource["price"] = round(
                    max(
                        res.max_price/max(resource["amount"] * res.k, 1),
                        res.min_price
                    )
                )

    def produce_resources(self):
        for point in self.points:
            if point.storage[0]['amount'] > 0:
                point.storage[point.base_resource]['amount'] += self.resources[point.base_resource].production

    def consume_resources(self):
        for point in self.points:
            for idx in range(len(point.storage)):
                if idx != point.base_resource:
                    if point.storage[idx]['amount'] > 0:
                        point.storage[idx]['amount'] -= max(round(point.storage[idx]['amount']/5), 1)

    def current_time(self):
        return datetime.now() - self.start_time


