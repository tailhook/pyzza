from layout import TopLevel, RoundRect, Poly, Layout, State, Rel, Constraint
from flash.events import Event

def play(name, color, states):
    return Poly(name, color, [
        [[0.0, 0], [1, 0.5], [0, 1.0]],
        ], states)

def pause(name, color, states):
    return Poly(name, color, [
        [[0, 0], [0.4, 0], [0.4, 1], [0, 1]],
        [[0.6, 0], [1, 0], [1, 1], [0.6, 1]],
        ], states)

def stop(name, color, states):
    return Poly(name, color, [
        [[0, 0], [1, 0], [1, 1], [0, 1]],
        ], states)

@package('layout.sample')
class Main(TopLevel):
    def __init__(self):
        self.layout = Layout([
            RoundRect('bg', 0xC0C0C0, 18, {
                'normal': State('normal',
                    Rel(0.2, 0),
                    Rel(0.8, 1),
                    Constraint(0.5, 0.5, 200, 32, 1000, 32)),
                }),
            RoundRect('play_bg', 0xFF0000, 10, {
                'normal': State('normal',
                    Rel(0, 0, 'bg', 'bg', 4, 4),
                    Rel(0, 1, 'bg', 'bg', 28, -4),
                    Constraint(0.5, 0.5, None, None, 1000, 32)),
                }),
            play('play_icon', 0xFFFFFF, {
                'normal': State('normal',
                    Rel(0.3, 0.3, 'play_bg', 'play_bg'),
                    Rel(0.7, 0.7, 'play_bg', 'play_bg')),
                }),
            RoundRect('pause_bg', 0xFF0000, 10, {
                'normal': State('normal',
                    Rel(1, 0, 'play_bg', 'play_bg', 4, 0),
                    Rel(1, 1, 'play_bg', 'play_bg', 28, 0)),
                }),
            pause('pause_icon', 0xFFFFFF, {
                'normal': State('normal',
                    Rel(0.3, 0.3, 'pause_bg', 'pause_bg'),
                    Rel(0.7, 0.7, 'pause_bg', 'pause_bg')),
                }),
            RoundRect('stop_bg', 0xFF0000, 10, {
                'normal': State('normal',
                    Rel(1, 0, 'pause_bg', 'pause_bg', 4, 0),
                    Rel(1, 1, 'pause_bg', 'pause_bg', 28, 0)),
                }),
            stop('stop_icon', 0xFFFFFF, {
                'normal': State('normal',
                    Rel(0.3, 0.3, 'stop_bg', 'stop_bg'),
                    Rel(0.7, 0.7, 'stop_bg', 'stop_bg')),
                }),
            ])
        super().__init__()
