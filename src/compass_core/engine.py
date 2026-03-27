from .decorators import compass_public


@compass_public
class CompassRunner:
    def __init__(self):
        self.version = "0.1.0"

    @compass_public
    def run(self):
        print(f"Compass Framework (v{self.version}) is active and isolated.")