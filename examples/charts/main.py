from charts import LeftVerticalAxis, BottomHorizontalAxis, LineChart
from charts import RectangleData
from layout import Layout, CenteredLine, TopLevel, State
from flash.text.engine import ElementFormat

COUNT=100
testdata = []
for i in range(COUNT):
    testdata.push([i, i*i, COUNT*COUNT-i*i])

@package('charts')
class Style:
    data_series_colors = [
        0x0000FF,
        0xFF0000,
        ]
    def __init__(self):
        pass

Style.prototype.data_series_colors = Style.data_series_colors

@package('charts')
class Main(TopLevel):
    def __init__(self):
        fmt = ElementFormat(None, 14, 0x000000)
        data = RectangleData(testdata)
        self.layout = Layout([
            LineChart(data, Style(), 'chart', {
                'normal': State.parse(
                'normal:(0,0+40+40)-(1,1-40-40)[100-,50-]'),
                }),
            BottomHorizontalAxis(data, 'xaxis', {
                'normal': State.parse(
                'normal:<chart>(0,1)-(1,1+0+20)'),
                }),
            LeftVerticalAxis(data, 'yaxis', {
                'normal': State.parse(
                'normal:<chart>(0,0-20+0)-(0,1)'),
                }),
            CenteredLine(fmt, "Some test data", 'title', {
                'normal': State.parse(
                'normal:<chart>(0,0-30)-(1,0)')
                }),
            ])
        super().__init__()

