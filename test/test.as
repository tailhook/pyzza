package {
    public class test {
        public function test(p1:String) {
            testfunc(10);
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
