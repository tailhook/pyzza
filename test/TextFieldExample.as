package {
    import flash.display.Sprite;
    import flash.text.TextField;
    //~ import flash.text.TextFieldAutoSize;
    import flash.text.TextFormat;

    public class TextFieldExample extends Sprite {
        private var label:TextField;

        public function TextFieldExample() {
            label = new TextField();
            //~ label.autoSize = TextFieldAutoSize.LEFT;
            label.background = true;
            label.border = true;
            label.text = testfunc({a:3, b:2});
            addChild(label);
        }

        public function test1():TextField {
            return this.label;
        }

        public function test2():TextField {
            return label;
        }
    }
}

function testfunc(...args):String {
    return args[0]['a'] + args[0].b
}
