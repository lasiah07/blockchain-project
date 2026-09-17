import random


class ProofOfStake:

    def __init__(self, validators):
        self.validators = validators

    def select_validator(self):

        names = list(self.validators.keys())
        stakes = list(self.validators.values())

        selected_validator = random.choices(
            names,
            weights=stakes,
            k=1
        )[0]

        return selected_validator