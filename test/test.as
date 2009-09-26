package {
    import flash.text.TextField;
    //~ import flash.text.TextFieldAutoSize;
    import flash.display.Sprite;

    public class test extends Sprite {
        private var label:TextField;
        public function test(p1:String) {
            label = new TextField();
            //~ label.autoSize = TextFieldAutoSize.LEFT;
            label.background = true;
            label.border = true;
            label.text = "HELLO";
            addChild(label);
        }
        public function test2(p1:String):void {
            testfunc(11);
        }
    }
}

function testfunc(param:*):* {
    return param.a*param.b+param.c;
}

function testfunc1():* {
    return 2;
}
