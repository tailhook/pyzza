package {
    import flash.text.TextField;
    import flash.display.Sprite;

    public class test extends Sprite {
        public function test() {
            super();
            var label:TextField = new TextField();
            label.background = true;
            label.border = true;
            if(Math.random() >= 0.5) {
                label.text = "HELLO";
            } else {
                label.text = "WORLD";
            }
            this.addChild(label);
        }
    }
}
