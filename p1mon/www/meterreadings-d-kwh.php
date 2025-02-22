<?php
include_once '/p1mon/www/util/page_header.php';
include_once '/p1mon/www/util/p1mon-util.php';  
include_once '/p1mon/www/util/page_menu.php';
include_once '/p1mon/www/util/check_display_is_active.php';
include_once '/p1mon/www/util/weather_info.php';
include_once '/p1mon/www/util/pageclock.php';
include_once '/p1mon/www/util/fullscreen.php';
include_once '/p1mon/www/util/page_menu_header_meterreadings.php';
include_once '/p1mon/www/util/textlib.php';

if ( checkDisplayIsActive(62) == false) { return; }
?>
<!doctype html>
<html lang="nl">
<head>
<meta name="robots" content="noindex">
<title>P1monitor historie dag meterstanden</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<link rel="shortcut icon" type="image/x-icon" href="/favicon.ico">
<link type="text/css" rel="stylesheet" href="./css/p1mon.css">
<link type="text/css" rel="stylesheet" href="./font/roboto/roboto.css">

<script defer src="./font/awsome/js/all.js"></script>
<script src="./js/jquery.min.js"></script>
<script src="./js/highstock-link/highstock.js"></script>
<script src="./js/highstock-link/highcharts-more.js"></script>
<script src="./js/highstock-link/modules/accessibility.js"></script>
<script src="./js/hc-global-options.js"></script>
<script src="./js/p1mon-util.js"></script>

<script>
"use strict"; 
// change items with the marker #PARAMETER
var consumptionKwhLow       = [];
var consumptionKwhHigh      = [];
var consumptionKwhTotal     = [];
var productionKwhLow        = [];
var productionKwhHigh       = [];
var productionKwhTotal      = [];

var productionKwhLowGross   = [];
var productionKwhHighGross  = [];
var productionKwhTotalGross = [];

var seriesOptions       = [];
var recordsLoaded       = 0;
var initloadtimer;
var Gselected           = 0;
var GselectText         = [ '1 week','1 maand','1 jaar','totaal' ]; // #PARAMETER
var GseriesVisibilty    = [ true,true,true,true,true,true,true,true,true ];
var mins                = 1;
var secs                = mins * 60;
var currentSeconds      = 0;
var currentMinutes      = 0;


function readJsonApiHistoryDay(){ 
    $.getScript( "/api/v1/powergas/day", function( data, textStatus, jqxhr ) {
      try {
        var jsondata = JSON.parse(data); 
        var item;
        recordsLoaded = jsondata.length;

        //empty the arrays.
        consumptionKwhLow.length       = 0;
        consumptionKwhHigh.length      = 0;
        consumptionKwhTotal.length     = 0;
        productionKwhLow.length        = 0;
        productionKwhHigh.length       = 0;
        productionKwhTotal.length      = 0;
        productionKwhLowGross.length   = 0;
        productionKwhHighGross.length  = 0;
        productionKwhTotalGross.length = 0;

        for (var j = jsondata.length; j > 0; j--){    
            item    = jsondata[ j-1 ];
            item[1] = item[1] * 1000; // highchart likes millisecs.

            consumptionKwhLow.push(       [ item[1], item[2] ] );
            consumptionKwhHigh.push(      [ item[1], item[3] ] );
            consumptionKwhTotal.push(     [ item[1], ( item[2] + item[3] ) ] );
            productionKwhLow.push(        [ item[1], item[4] ] );
            productionKwhHigh.push(       [ item[1], item[5] ] );
            productionKwhTotal.push(      [ item[1], ( item[4] + item[5] ) ] );
            // the null will be filled by another ajax call.
            productionKwhLowGross.push(   [ item[1], null ] );
            productionKwhHighGross.push(  [ item[1], null ] );  
            productionKwhTotalGross.push( [ item[1], null ] );
        } 
        readJsonApiHistoryPowerDay()
      } catch(err) {
        console.log( err )
      }
   });
}

function readJsonApiHistoryPowerDay(){ 
    $.getScript( "/api/v1/powerproduction/day", function( data, textStatus, jqxhr ) {
        try {
        var jsondata = JSON.parse(data); 
        var item;

        for( var j=0; j<jsondata.length; j++ ) {
            for ( var n=0; n<productionKwhHighGross.length; n++) {
                if ( (jsondata[j][1] * 1000) == productionKwhHighGross[n][0] ) {
                    productionKwhHighGross[n][1]  = jsondata[j][8];
                    productionKwhLowGross[n][1]   = jsondata[j][9];
                    productionKwhTotalGross[n][1] = jsondata[j][10];
                }
            }
        }
        updateData(); 
      } catch(err) {}
   });
}

// change items with the marker #PARAMETER
function createMeterReadingsChart() {
  Highcharts.stockChart('meterReadingChart', {
  exporting: { enabled: false },
  lang: {
    noData: "Geen gegevens beschikbaar."
  },
  noData: {
    style: { 
      fontFamily: 'robotomedium',   
        fontWeight: 'bold',     
          fontSize: '25px',
          color: '#10D0E7'        
   }
  },
  chart: {
    //ignoreHiddenSeries: false,
    style: {
      fontFamily: 'robotomedium'
    },
    backgroundColor: '#ffffff',
    borderWidth: 0
  },   
  title: {
            margin: 35,
            text: 'placeholder', 
            style: {
                color: '#FFFFFF',
                fontWeight: 'bold',
                fontSize: "10px"
            }
  },
  navigator: {
    xAxis: {
      minTickInterval:  1 * 24 * 3600000, 
      maxRange:        25 * 365 * 24 * 3600000,
      type: 'datetime',
      dateTimeLabelFormats: {
        day: '%a.<br>%d %B<br/>%Y',
        month: '%B<br/>%Y',
        year: '%Y'
      }  
    },  
    enabled: true,
    outlineColor: '#384042',
    outlineWidth: 1,
    handles: {
      backgroundColor: '#384042',
      borderColor: '#6E797C'
    },
    
  },   
  xAxis: {
   type: 'datetime',
   minTickInterval: 1   * 24 * 3600000, 
   range:          5000 * 24 * 3600000,
   minRange:       7  * 24 * 3600000,
   maxRange:       61 * 24 * 3600000,
   dateTimeLabelFormats: {
     day: '%a.<br>%d %b<br/>%Y',
     hour: '%a.<br>%H:%M',
     year: '%Y'
   },
   lineColor: '#6E797C',
   lineWidth: 1, 
   events: {
        setExtremes: function(e) {
        if(typeof(e.rangeSelectorButton)!== 'undefined') {
         for (var j = 0;  j < GselectText.length; j++){    
           if ( GselectText[j] == e.rangeSelectorButton.text ) {
             toLocalStorage('select-meterreadings-d-kwh-index',j); // #PARAMETER
             break;
           }
         }
       }
     }
   },   
  },
  yAxis: [
    { // kWh axis
        showEmpty: false,
        tickAmount: 7,
        opposite: false,
        offset: null,
        gridLineDashStyle: 'longdash',
        gridLineColor: '#6E797C',
        gridLineWidth: 1,
        labels: {
            format: '{value} kWh',
                style: {
                    color: '#6E797C',
                },
            },
        title: {
        text: null, 
        },
    },
  ],
  tooltip: {
       useHTML: false,
        style: {
            padding: 3,
            color: '#6E797C'
        },
      formatter: function() {
        
        var s = '<b>'+ Highcharts.dateFormat('%A, %Y-%m-%d', this.x) +'</b>';
        var d = this.points;
           
        for (var i=0,  tot=d.length; i < tot; i++) {
                    
                if ( d[i].series.userOptions.name === 'dal verbruik' ) {
                    s += '<br/><span style="color:#CEA731">Dal verbruik: </span>' + d[i].y.toFixed(3) + " kWh";
                        //console.log( d[i].y )
                }
                if ( d[i].series.userOptions.name === 'piek verbruik' ) {
                    s += '<br/><span style="color:#FFC311">Piek verbruik: </span>' + d[i].y.toFixed(3) + " kWh";
                    //console.log( d[i].y )
                }
                if ( d[i].series.userOptions.name === 'totaal verbruik' ) {
                    s += '<br/><span style="color:#6E797C">Totaal verbruik: </span>' + d[i].y.toFixed(3) + " kWh";
                    //console.log( d[i].y )
                }
                if ( d[i].series.userOptions.name === 'netto dal geleverd' ) {
                    s += '<br/><span style="color:#7FAD1D">Netto dal geleverd: </span>' + d[i].y.toFixed(3) + " kWh";
                    //console.log( d[i].y )
                }   
                if ( d[i].series.userOptions.name === 'netto piek geleverd' ) {
                    s += '<br/><span style="color:#98D023">Netto piek geleverd: </span>' + d[i].y.toFixed(3) + " kWh";
                    //console.log( d[i].y )
                }
                if ( d[i].series.userOptions.name === 'netto totaal geleverd' ) {
                    s += '<br/><span style="color:#6E797C">Netto totaal geleverd: </span>' + d[i].y.toFixed(3) + " kWh";
                    //console.log( d[i].y )
                }
                if ( d[i].series.userOptions.name === 'bruto dal geleverd' ) {
                    s += '<br/><span style="color:#7FAD1D">Bruto dal geleverd: </span>' + d[i].y.toFixed(3) + " kWh";
                    //console.log( d[i].y )
                }    
                if ( d[i].series.userOptions.name === 'bruto piek geleverd' ) {
                    s += '<br/><span style="color:#98D023">Bruto piek geleverd: </span>' + d[i].y.toFixed(3) + " kWh";
                    //console.log( d[i].y )
                }
                if ( d[i].series.userOptions.name === 'bruto totaal geleverd' ) {
                    s += '<br/><span style="color:#6E797C">Bruto totaal geleverd: </span>' + d[i].y.toFixed(3) + " kWh";
                    //console.log( d[i].y )
                }
        }
        //console.log (s)
        return s;
      },
      backgroundColor: '#F5F5F5',
      borderColor: '#DCE1E3',
      crosshairs: [true, true],
      borderWidth: 1
    },
    rangeSelector: { // #PARAMETER
      inputEnabled: false,
       buttonSpacing: 5, 
       selected : Gselected,
       buttons: [{
        type: 'day',
        count: 7,
        text: GselectText[0]
       },{
         type: 'month',
         count: 1,
         text: GselectText[1]
       },{
        type: 'year',
        count: 1,
        text: GselectText[2]
       }, {
        type: 'all',
        //count: 3,
        text: GselectText[3]
       }],
       buttonTheme: { 
        r: 3,
        fill: '#F5F5F5',
        stroke: '#DCE1E3',
        'stroke-width': 1,
        width: 65,
        style: {
          color: '#6E797C',
          fontWeight: 'normal'
        },
        states: {
          hover: {
            fill: '#F5F5F5',
            style: {
              color: '#10D0E7'
            }
          },
          select: {
            fill: '#DCE1E3',
            stroke: '#DCE1E3',
            'stroke-width': 1,
            style: {
              color: '#384042',
              fontWeight: 'normal'
            }
          }
        }
      }  
    },
    legend: {
        y: -38,
        symbolHeight: 12,
        symbolWidth: 12,
        symbolRadius: 3,
        borderRadius: 5,
        borderWidth: 1,
        backgroundColor: '#DCE1E3',
        symbolPadding: 3,
        enabled: true,
        align: 'right',
        verticalAlign: 'top',
        floating: true,
        itemStyle: {
            color: '#6E797C'
        },
        itemHoverStyle: {
            color: '#10D0E7'
        },
        itemDistance: 5
    },
    series: [ 
    {
        yAxis: 0,
        visible: GseriesVisibilty[0],
        showInNavigator: true,
        name: 'dal verbruik',
        type: 'spline',
        color: '#CEA731',
        data: consumptionKwhLow,
    },
    {
        yAxis: 0,
        visible: GseriesVisibilty[1],
        showInNavigator: true,
        name: 'piek verbruik',
        type: 'spline',
        color: '#FFC311',
        data: consumptionKwhHigh,
    },
    {
        yAxis: 0,
        dashStyle: 'ShortDashDotDot',
        visible: GseriesVisibilty[2],
        showInNavigator: true,
        name: 'totaal verbruik',
        type: 'spline',
        color: '#E9B620',
        data: consumptionKwhTotal,
    },
    {
        yAxis: 0,
        visible: GseriesVisibilty[3],
        showInNavigator: true,
        name: 'netto dal geleverd',
        type: 'spline',
        color: '#7FAD1D',
        data: productionKwhLow,
    },
    {
        yAxis: 0,
        visible: GseriesVisibilty[4],
        showInNavigator: true,
        name: 'netto piek geleverd',
        type: 'spline',
        color: '#98D023',
        data: productionKwhHigh,
    },
    {
        yAxis: 0,
        dashStyle: 'ShortDashDotDot',
        visible: GseriesVisibilty[5],
        showInNavigator: true,
        name: 'netto totaal geleverd',
        type: 'spline',
        color: '#8ABD20',
        data: productionKwhTotal,
    },
    {
        yAxis: 0,
        visible: GseriesVisibilty[6],
        showInNavigator: true,
        name: 'bruto dal geleverd',
        type: 'spline',
        color: '#7FAD1D',
        data: productionKwhLowGross,
        zIndex: 0,
    },
    {
        yAxis: 0,
        visible: GseriesVisibilty[7],
        showInNavigator: true,
        name: 'bruto piek geleverd',
        type: 'spline',
        color: '#98D023',
        data: productionKwhHighGross,
    },
    {
        yAxis: 0,
        dashStyle: 'ShortDashDotDot',
        visible: GseriesVisibilty[8],
        showInNavigator: true,
        name: 'bruto totaal geleverd',
        type: 'spline',
        color: '#8ABD20',
        data: productionKwhHighGross,
    }
    ],
    plotOptions: {
      series: {
        events: {
          legendItemClick: function () {
            //console.log('legendItemClick index='+this.index);
            
            if ( this.index === 0 ) {
              toLocalStorage('meterreadings-d-consumptionKwhLow',!this.visible); // #PARAMETER
            }
            if ( this.index === 1 ) {
              toLocalStorage('meterreadings-d-consumptionKwhHigh',!this.visible); // #PARAMETER
            }
            if ( this.index === 2 ) {
              toLocalStorage('meterreadings-d-consumptionKwhTotal',!this.visible); // #PARAMETER
            }
            if ( this.index === 3 ) {
              toLocalStorage('meterreadings-d-productionKwhLow',!this.visible); // #PARAMETER
            }
            if ( this.index === 4 ) {
              toLocalStorage('meterreadings-d-productionKwhHigh',!this.visible); // #PARAMETER
            }
            if ( this.index === 5 ) {
              toLocalStorage('meterreadings-d-productionKwhTotal',!this.visible); // #PARAMETER
            }
            if ( this.index === 6 ) {
              toLocalStorage('meterreadings-d-productionKwhLowGross',!this.visible); // #PARAMETER
            }
            if ( this.index === 7 ) {
              toLocalStorage('meterreadings-d-productionKwhHighGross',!this.visible); // #PARAMETER
            }
            if ( this.index === 8 ) {
              toLocalStorage('meterreadings-d-productionKwhHTotalGross',!this.visible); // #PARAMETER
            }
          }
        }
      }
    },
  });
  
}

function updateData() {
    if (recordsLoaded !== 0 ) {
      hideStuff('loading-data');
    }
    // console.log("updateData()");
    var chart = $('#meterReadingChart').highcharts();

    if( typeof(chart) !== 'undefined') {
        chart.series[0].setData( consumptionKwhLow );
        chart.series[1].setData( consumptionKwhHigh );
        chart.series[2].setData( consumptionKwhTotal );
        chart.series[3].setData( productionKwhLow );
        chart.series[4].setData( productionKwhHigh );
        chart.series[5].setData( productionKwhTotal );
        chart.series[6].setData( productionKwhLowGross );
        chart.series[7].setData( productionKwhHighGross );
        chart.series[8].setData( productionKwhTotalGross );
    }
}

function DataLoop() {
    currentMinutes = Math.floor(secs / 60);
    currentSeconds = secs % 60;
    if(currentSeconds <= 9) { currentSeconds = "0" + currentSeconds; }
    secs--;
    document.getElementById("timerText").innerHTML = zeroPad(currentMinutes,2) + ":" + zeroPad(currentSeconds,2);
    if(secs < 0 ) { 
        mins = 1;  
        secs = mins * 60;
        currentSeconds = 0;
        currentMinutes = 0;
        colorFader("#timerText","#0C7DAD");
        readJsonApiHistoryDay();
    }
    setTimeout('DataLoop()',1000);
}

$(function() {
  toLocalStorage('meterreadings-menu',window.location.pathname);

  GseriesVisibilty[0] = JSON.parse(getLocalStorage('meterreadings-d-consumptionKwhLow'));       // #PARAMETER
  GseriesVisibilty[1] = JSON.parse(getLocalStorage('meterreadings-d-consumptionKwhHigh'));      // #PARAMETER
  GseriesVisibilty[2] = JSON.parse(getLocalStorage('meterreadings-d-consumptionKwhTotal'));     // #PARAMETER
  GseriesVisibilty[3] = JSON.parse(getLocalStorage('meterreadings-d-productionKwhLow'));        // #PARAMETER
  GseriesVisibilty[4] = JSON.parse(getLocalStorage('meterreadings-d-productionKwhHigh'));       // #PARAMETER
  GseriesVisibilty[5] = JSON.parse(getLocalStorage('meterreadings-d-productionKwhTotal'));      // #PARAMETER
  GseriesVisibilty[6] = JSON.parse(getLocalStorage('meterreadings-d-productionKwhLowGross'));   // #PARAMETER
  GseriesVisibilty[7] = JSON.parse(getLocalStorage('meterreadings-d-productionKwhHighGross'));  // #PARAMETER
  GseriesVisibilty[8] = JSON.parse(getLocalStorage('meterreadings-d-productionKwhTotalGross')); // #PARAMETER

  Gselected = parseInt(getLocalStorage('select-meterreadings-d-kwh-index'),10); // #PARAMETER

  Highcharts.setOptions({
   global: {
    useUTC: false
    }
  });
  screenSaver( <?php echo config_read(79);?> ); // to enable screensaver for this screen.
  secs = 0;
  createMeterReadingsChart();
  DataLoop();
});

</script>
</head>
<body title="<?php echo strIdx( 99 ); #PARAMETER ?>"> 

<?php page_header();?>

<div class="top-wrapper-2">
    <div class="content-wrapper pad-13">
       <!-- header 2 -->
        <?php pageclock(); ?>
        <?php page_menu_header_meterreadings( 0 ) ?>
        <?php weather_info(); ?>
    </div>
</div>

<div class="mid-section">
    <div class="left-wrapper">
        <?php page_menu( 8 ); ?>
        <div id="timerText" class="pos-8 color-timer"></div>
        <?php fullscreen(); ?>
    </div> 
    <div class="mid-content-2 pad-13">
    <!-- links -->
        <div class="frame-2-top">
            <span class="text-2">meterstanden per dag</span>
        </div>
        <div class="frame-2-bot"> 
        <div id="meterReadingChart" style="width:100%; height:480px;"></div>
        </div>
</div>
</div>
<div id="loading-data"><img src="./img/ajax-loader.gif" alt="Even geduld aub." height="15" width="128"></div>

</body>
</html>