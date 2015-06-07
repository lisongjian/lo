/** @preserve Copyright 2010-2014 . All Rights Reserved. */
/**
 通用方法api
 -----------
 */
;(function(win, doc, $) {
    /** 私有属性
     -----------------------------------------------------------------*/
    var API = {};

    /** 公有属性&方法
     -----------------------------------------------------------------*/
    API = {
        timestamp  :  0,           // 时间戳

        /**
         *  =ping
         *  @about    ping 某个 URL
         *
         *  @param    {string}  u  地址
         */
        ping: function(u) {
            $('<img />').attr('src', u);
        },


        /**
         *  =host
         *  @about    获取当前 host
         */
        host: function() {
            return "http://"+ win.location.host;
        },


        /**
         *  =timeGap
         *  @about    获取间隔时间
         *
         *  @param    {number}  when
         */
        timeGap: function(w) {
            if (w) {
                return +new Date() - this.timestamp;
            }
            else {
                this.timestamp = +new Date();
                return this.timestamp;
            }
        },


        /**
         *  =getRequest
         *  @about    获取 GET 参数
         *
         *  @return   {object}   参数集合
         */
        getRequest: function()  {
            var url = win.location.search,  // 获取url中"?"后面的字符串
                i = 0,
                args, arg,
                back = {};

            if (url == '') return 0;

            if ( url.indexOf('?') != -1 ) {
                args = url.substr(1).split('&');

                for (; i < args.length; i++) {
                    arg = args[i].split('=');
                    back[ arg[0] ] = arg[1];
                }
            }

            return arguments[0] ? back[arguments[0]] : back;
        },


        /**
         *  =getSignature
         *  @about    获取参数签名
         *
         *  @param    {json}    params
         *  @param    {string}  access_key
         *  @return   {string}
         */
        getSignature: function(params, access_key) {
            var str = '', tmp_arr = [];
            for (var p in params) tmp_arr.push(p);
            // 参数根据其参数名进行降序排序
            tmp_arr.sort();
            // 遍历排序后的参数，拼接 key=value 字符串
            for (var i = 0; i < tmp_arr.length; i++)
                str += tmp_arr[i] + '=' + this.encode(params[tmp_arr[i]]);
            // 在拼接字符串后再接上 access_key
            str += access_key;
            // 通过 MD5 算法为签名字符串生成一个 MD5 签名，该签名就是 sign 参数值
            return MD5.hex_md5(str);
        },


        /**
         *  =getUrlSignature
         *  @about    获取带参数签名的完整地址
         *
         *  @param    {string}  url
         *  @param    {json}    params
         *  @param    {string}  access_key
         *  @return   {string}
         */
        getUrlSignature: function(url, params, access_key) {
            var str = '', tmp_arr = [];
            // 生成签名
            params['sign'] = this.getSignature(params, access_key);
            // 拼接参数
            for (var p in params) tmp_arr.push(p +'='+ this.encode(params[p]));
            // 拼接链接
            str += url +'?'+ tmp_arr.join('&');
            return str;
        },


        /**
         *  =setItem
         *  @about    储存本地数据
         *
         *  @param    {string}  key    数据名称
         *  @param    {boolean} value  数据
         */
        setItem: function(key, value) {
            if ($.isArray(value) || $.isPlainObject(value)) value = JSON.stringify(value);
            try {
                win.localStorage.setItem(key, value);
            } catch(e) {
                // FIXED 私密模式无法使用 Storage
                if ($("#"+ key).length) {
                    $("#"+ key).text(value);
                }
                else {
                    $("<script />", { id: key, text: value, type: "text/template"}).appendTo('body');
                }
            }
            return 1;
        },


        /**
         *  =getItem
         *  @about    获取本地存储数据
         *
         *  @param    {string}  key  数据名称
         *  @param    {boolean} hl   是否处理数据
         *  @return   {string/json}
         */
        getItem: function(key, hl) {
            hl = hl || 0;
            try {
                win.localStorage.test = 2; // 检测是否 safari 无痕模式

                var value = win.localStorage.getItem(key);
                if (value) {
                    return hl ? JSON.parse(value) : value;
                }
            } catch(e) {
                // FIXED 私密模式无法使用 Storage
                var value = $("#"+ key).text();
                if (value) {
                    return hl ? JSON.parse(value) : value;
                }
            }
            return null;
        },


        /**
         *  @about    获取位置信息
         */
        getScrollTop: function() { return window.scrollY; }, // 上滚动距离
        getWidth: function() { return screen.width || win.innerWidth; },
        getHeight: function() { return screen.height || win.innerHeight; },


        /**
         * @about    随机数
         */
        random: function(n) { return parseInt(Math.random() * n); },


        /**
         *  =encode
         *  @about    字符串 encode
         *
         *  @param    {string}  s 需要 encode 的字符串
         *  @return   {string}
         */
        encode: function(s) { return encodeURIComponent(s); },


        /**
         *  =decode
         *  @about    编码decode
         *
         *  @param    {string}  s  需要decode的字符串
         *  @return   {string}
         */
        decode: function(s) { return decodeURIComponent(s); },


        /**
         *  =is empty
         *  @about     是否为空
         *
         *  @params    {object}  obj
         */
        isEmpty: function(obj) {
            for (var n in obj) return false;
            return true;
        },


        /**
         *  =escape
         *  @about    （包含中文的）数据容错处理
         *
         *  @param    {string}  s  需要处理的数据字符串
         *  @return   {json}    c  1，数据为空
         *                         2, 数据无法解析
         *
         escape: function(s) {
            var d = { c: 1 };

            if (!!s) {
                // 数据容错处理
                try {
                    d = s.replace(/(\r\n|\r|\n)/g, '\\n'); // 特殊字符处理
                    d = JSON.parse(d);
                }
                catch(e) {
                    // 输出数据错误信息
                    API._log('Data Error:'+ e);
                    d.c = 2;
                }
            }

            return d;
        },


         /**
         *  =number Format
         *  @about    数字格式化
         *
         *  @param    {number}  num   需要格式化的string
         *  @param    {string}  unit  积分单位
         */
        numFormat: function(num, unit) {
            // 保留 fixed 小数位数
            num = parseFloat(num).toFixed( (arguments[1] || 0) );

            // 若单位为元，进行特殊处理
            unit = unit || '';
            if (unit == '元') { num /= 100; }

            // 加上逗号
            num += '';
            var x = num.split('.'),
                x1 = x[0],
                x2 = (x.length > 1) ? ('.' + x[1]) : '',
                rgx = /(\d+)(\d{3})/;

            while (rgx.test(x1)) x1 = x1.replace(rgx, '$1' + ',' + '$2');

            return x1 + x2;
        },


        /**
         *  =string Format
         *  @about    字符串格式化
         *
         *  @param    {string}  d    需要格式化的string
         *  @param    {all}     1~n  {n} 替换内容
         *  @return   {string}       格式化后的string
         */
        strFormat: function(s) {
            if (arguments.length == 0) return null;

            var args = Array.prototype.slice.call(arguments, 1);
            return s = s.replace(/\{(\d+)\}/g, function(m, i) {
                return args[i];
            });
        },


        /**
         *  =funTransitionHeight
         *  @about 有动画地变化高度
         *
         *  @param element
         *  @param time
         */
        funTransitionHeight: function(element, time) { // time, 数值，可缺省
            if (typeof window.getComputedStyle == "undefined") return;

            var height = window.getComputedStyle(element).height;
            element.style.height = "auto";
            var targetHeight = window.getComputedStyle(element).height;
            element.style.height = height;
            setTimeout(function() {
                if (time) element.style.transition = "height "+ time +"ms,opacity " + time + "ms";
                element.style.height = targetHeight;
                element.style.opacity = 1;
            }, 15);
        },


        /**
         *  =detectEventSupport
         *  @about   是否支持事件
         *
         *  @param   eventName  事件名字
         *  @return  {boolean}
         */
        detectEventSupport: function(eventName) {
            var tempElement = document.createElement('div'),
                isSupported;

            eventName = 'on' + eventName;
            isSupported = (eventName in tempElement); // 使用第一种方式
            // 如果第一种方式行不通，那就来看看它是不是已知事件类型
            if(!isSupported) {
                tempElement.setAttribute(eventName, 'xxx');
                isSupported = typeof tempElement[eventName] === 'function';
            }
            // 清除掉动态创建的元素，以便内存回收
            tempElement = null;
            // 返回检测结果
            return isSupported;
        }

    };

    win.API = API;

    /**
     =template
     @about    简易模板

     @usage

     HTML:
     <script type="text/template" id="tpl-article"><h1>{{title}}</h1></script>

     JavaScript:
     $('#tpl-article').tmpl(data).appendTo($item);
     */
    (function($){
        $.fn.tmpl = function(d) {
            var s = $(this[0]).html().trim();
            if ($.isArray(d)) {
                var li = '',
                    tm = {}, i = 0, len = d.length;
                for (; i < len; i++) {
                    tm = d[i];
                    li += s.replace(/\{\=(\w+)\}/g, function(all, match) {
                        return tm[match];
                    });
                }
                s = li;
            }
            else {
                s = s.replace(/\{\=(\w+)\}/g, function(all, match) {
                    return d[match];
                });
            }
            return $(s);
        };
    })($);


    /**
     =pages
     @about    页面切换
     */
    (function($) {
        /**
         *  @param    {string}    p  页面标识
         *  @param    {function}  f  后续执行
         */
        $.fn.pages = function(p, before, after) {
            $(this).each(function(index) {
                var $this = $(this);
                if ( $this.data('page') === p ) {
                    setTimeout(function() {
                        (before || function() {})($this);
                        $this.attr('class', 'ui-page ui-page-active fade in');
                        setTimeout(function() {
                            $this.removeClass('fade in');
                        }, 225);
                        (after || function() {})($this);
                    }, 124);
                }
                else {
                    if ( $this.hasClass('ui-page-active') ) {
                        $this.attr('class', 'ui-page ui-page-active fade out');
                        setTimeout(function() {
                            $this.removeClass('ui-page-active fade out');
                        }, 125);
                    }
                }
            });
        };
    })($);
})(window, document, Zepto);