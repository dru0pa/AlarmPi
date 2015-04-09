import wink
import json
import logging

log = logging.getLogger('root')

class Wink:

    def __init__(self):
        self.w = wink.init("config.cfg")

    def activate(self, group_id, state, brightness):
        activate_group = json.dumps({
            "desired_state": {
                "powered":state,
                "brightness":brightness
            }
        })
        log.info("Setting Wink group_id {0} to state {1} and brightness {2}".format(group_id,state,brightness))
        self.w.activate_group(group_id,activate_group)


if __name__ == '__main__':
    winker = Wink()
    print json.dumps(winker.w.get_groups(), indent=4, separators=(',', ': '))
    json.dumps(winker.activate("2901669",bool(),0), indent=4, separators=(',', ': '))