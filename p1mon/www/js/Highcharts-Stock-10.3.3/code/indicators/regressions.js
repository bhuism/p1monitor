/*
 Highstock JS v10.3.3 (2023-01-20)

 Indicator series type for Highcharts Stock

 (c) 2010-2021 Kamil Kulig

 License: www.highcharts.com/license
*/
(function(d){"object"===typeof module&&module.exports?(d["default"]=d,module.exports=d):"function"===typeof define&&define.amd?define("highcharts/indicators/regressions",["highcharts","highcharts/modules/stock"],function(h){d(h);d.Highcharts=h;return d}):d("undefined"!==typeof Highcharts?Highcharts:void 0)})(function(d){function h(d,b,g,f){d.hasOwnProperty(b)||(d[b]=f.apply(null,g),"function"===typeof CustomEvent&&window.dispatchEvent(new CustomEvent("HighchartsModuleLoaded",{detail:{path:b,module:d[b]}})))}
d=d?d._modules:{};h(d,"Stock/Indicators/LinearRegression/LinearRegressionIndicator.js",[d["Core/Series/SeriesRegistry.js"],d["Core/Utilities.js"]],function(d,b){var g=this&&this.__extends||function(){var c=function(a,e){c=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(a,e){a.__proto__=e}||function(a,e){for(var c in e)e.hasOwnProperty(c)&&(a[c]=e[c])};return c(a,e)};return function(a,e){function l(){this.constructor=a}c(a,e);a.prototype=null===e?Object.create(e):(l.prototype=e.prototype,
new l)}}(),f=d.seriesTypes.sma,h=b.isArray,k=b.extend,m=b.merge;b=function(c){function a(){var a=null!==c&&c.apply(this,arguments)||this;a.data=void 0;a.options=void 0;a.points=void 0;return a}g(a,c);a.prototype.getRegressionLineParameters=function(a,c){var e=this.options.params.index,l=function(a,e){return h(a)?a[e]:a},b=a.reduce(function(a,e){return e+a},0),d=c.reduce(function(a,c){return l(c,e)+a},0);b/=a.length;d/=c.length;var m=0,f=0,k;for(k=0;k<a.length;k++){var g=a[k]-b;var n=l(c[k],e)-d;m+=
g*n;f+=Math.pow(g,2)}a=f?m/f:0;return{slope:a,intercept:d-a*b}};a.prototype.getEndPointY=function(a,c){return a.slope*c+a.intercept};a.prototype.transformXData=function(a,c){var e=a[0];return a.map(function(a){return(a-e)/c})};a.prototype.findClosestDistance=function(a){var c,e;for(e=1;e<a.length-1;e++){var b=a[e]-a[e-1];0<b&&("undefined"===typeof c||b<c)&&(c=b)}return c};a.prototype.getValues=function(a,c){var e=a.xData;a=a.yData;c=c.period;var b,d={xData:[],yData:[],values:[]},m=this.options.params.xAxisUnit||
this.findClosestDistance(e);for(b=c-1;b<=e.length-1;b++){var l=b-c+1;var f=b+1;var k=e[b];var g=e.slice(l,f);l=a.slice(l,f);f=this.transformXData(g,m);g=this.getRegressionLineParameters(f,l);l=this.getEndPointY(g,f[f.length-1]);d.values.push({regressionLineParameters:g,x:k,y:l});d.xData.push(k);d.yData.push(l)}return d};a.defaultOptions=m(f.defaultOptions,{params:{xAxisUnit:null},tooltip:{valueDecimals:4}});return a}(f);k(b.prototype,{nameBase:"Linear Regression Indicator"});d.registerSeriesType("linearRegression",
b);"";return b});h(d,"Stock/Indicators/LinearRegressionSlopes/LinearRegressionSlopesIndicator.js",[d["Core/Series/SeriesRegistry.js"],d["Core/Utilities.js"]],function(d,b){var g=this&&this.__extends||function(){var b=function(c,a){b=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(a,c){a.__proto__=c}||function(a,c){for(var b in c)c.hasOwnProperty(b)&&(a[b]=c[b])};return b(c,a)};return function(c,a){function e(){this.constructor=c}b(c,a);c.prototype=null===a?Object.create(a):(e.prototype=
a.prototype,new e)}}(),f=d.seriesTypes.linearRegression,k=b.extend,h=b.merge;b=function(b){function c(){var a=null!==b&&b.apply(this,arguments)||this;a.data=void 0;a.options=void 0;a.points=void 0;return a}g(c,b);c.prototype.getEndPointY=function(a){return a.slope};c.defaultOptions=h(f.defaultOptions);return c}(f);k(b.prototype,{nameBase:"Linear Regression Slope Indicator"});d.registerSeriesType("linearRegressionSlope",b);"";return b});h(d,"Stock/Indicators/LinearRegressionIntercept/LinearRegressionInterceptIndicator.js",
[d["Core/Series/SeriesRegistry.js"],d["Core/Utilities.js"]],function(d,b){var g=this&&this.__extends||function(){var b=function(c,a){b=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(a,c){a.__proto__=c}||function(a,c){for(var b in c)c.hasOwnProperty(b)&&(a[b]=c[b])};return b(c,a)};return function(c,a){function d(){this.constructor=c}b(c,a);c.prototype=null===a?Object.create(a):(d.prototype=a.prototype,new d)}}(),f=d.seriesTypes.linearRegression,k=b.extend,h=b.merge;b=function(b){function c(){var a=
null!==b&&b.apply(this,arguments)||this;a.data=void 0;a.options=void 0;a.points=void 0;return a}g(c,b);c.prototype.getEndPointY=function(a){return a.intercept};c.defaultOptions=h(f.defaultOptions);return c}(f);k(b.prototype,{nameBase:"Linear Regression Intercept Indicator"});d.registerSeriesType("linearRegressionIntercept",b);"";return b});h(d,"Stock/Indicators/LinearRegressionAngle/LinearRegressionAngleIndicator.js",[d["Core/Series/SeriesRegistry.js"],d["Core/Utilities.js"]],function(d,b){var g=
this&&this.__extends||function(){var b=function(c,a){b=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(a,c){a.__proto__=c}||function(a,c){for(var b in c)c.hasOwnProperty(b)&&(a[b]=c[b])};return b(c,a)};return function(c,a){function d(){this.constructor=c}b(c,a);c.prototype=null===a?Object.create(a):(d.prototype=a.prototype,new d)}}(),f=d.seriesTypes.linearRegression,h=b.extend,k=b.merge;b=function(b){function c(){var a=null!==b&&b.apply(this,arguments)||this;a.data=void 0;a.options=
void 0;a.points=void 0;return a}g(c,b);c.prototype.slopeToAngle=function(a){return 180/Math.PI*Math.atan(a)};c.prototype.getEndPointY=function(a){return this.slopeToAngle(a.slope)};c.defaultOptions=k(f.defaultOptions,{tooltip:{pointFormat:'<span style="color:{point.color}">\u25cf</span>{series.name}: <b>{point.y}\u00b0</b><br/>'}});return c}(f);h(b.prototype,{nameBase:"Linear Regression Angle Indicator"});d.registerSeriesType("linearRegressionAngle",b);"";return b});h(d,"masters/indicators/regressions.src.js",
[],function(){})});
//# sourceMappingURL=regressions.js.map