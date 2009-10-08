package {
    import flash.text.TextField;
    import flash.display.Sprite;

    public class test extends Sprite {
        public function test() {
            super();
            var label:TextField = new TextField();
            label.background = true;
            label.border = true;
            label.text = "HELLO";
            this.addChild(label);
        }
    }
}
