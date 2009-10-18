package {
    import flash.text.TextField;
    import flash.display.Sprite;

    public class test extends Sprite {
        public function test() {
            super();
            var label:TextField = new TextField();
            label.background = true;
            label.border = true;
            try {
                var val:Number = Math.random();
                if(val <= 0.3) {
                    label.text = "STRING1";
                } else if(val <= 0.6) {
                    label.text = "STRING2";
                } else {
                    throw "Catch me";
                }
            } catch(e:String) {
                label.text = "STRING3";
            }
            this.addChild(label);
        }
    }
}
