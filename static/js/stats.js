/*
Help function
*/
function min(x) {
  let value;
  for (let i = 0; i < x.length; i += 1) {
    if (value === undefined || x[i] < value) {
      value = x[i];
    }
  }
  if (value === undefined) {
    return NaN;
  }
  return value;
}

function max(x) {
  let value;
  for (let i = 0; i < x.length; i += 1) {
    if (value === undefined || x[i] > value) {
      value = x[i];
    }
  }
  if (value === undefined) {
    return NaN;
  }
  return value;
}

function isValidKeyArr(obj, keyArr) {
  for (const idx in keyArr) {
    const key = keyArr[idx];
    if (Object.keys(obj).indexOf(key) !== -1) {
      obj = obj[key];
    } else {
      return false;
    }
  }
  return true;
}

function isKey(obj, key) {
  return (Object.keys(obj).indexOf(key.toString()) !== -1);
}

/*
@return obj = {
  x: {
    y: value
  }
} when keyArr is [x, y]
*/
function setEmtToObj(obj, keyArr, value) {
  const copiedObj = JSON.parse(JSON.stringify(obj));
  let key;
  if (keyArr.length === 1) {
    key = keyArr[0];
    copiedObj[key] = value;
  } else {
    key = keyArr.shift();
    if (!isKey(copiedObj, key)) {
      copiedObj[key] = {};
    }
    const newObj = copiedObj[key];
    copiedObj[key] = setEmtToObj(newObj, keyArr, value);
  }
  return copiedObj;
}

function renameKey(obj, oKey, nKey) {
  Object.defineProperty(
    obj,
    nKey,
    Object.getOwnPropertyDescriptor(
      obj,
      oKey,
  ));
  delete obj[oKey];
}

function isEmtOfArr(arr, obj) {
  return (arr.indexOf(obj) !== -1);
}

function makeFormattedToArr(formattedObj) {
  const rArr = [];
  for (const label in formattedObj) {
    rArr.push(formattedObj[label]);
  }
  return rArr;
}


/*
 * Global Variables
 */
let firstCallGlobal = true;

/*
sDateGlobal: start date, manually
eDateGlobal: date of today
*/
let sDateGlobal = '2016-08-16';
let eDateGlobal = (new Date()).toISOString().substring(0, 10);
let serviceGlobal = 'all';
const atomicListGlobal = ['kaist-professor', 'kaist-employee'];

/* department data */
const deptData = {
  0: 'Undecided',
  3648: 'Bio and Brain Engineering',
  132: 'Biological Sciences',
  2222: 'Biomedical Science and Engineering Program',
  936: 'Business',
  33: 'Capstone Design',
  451: 'Chemical and Biomolecular Engineering',
  150: 'Chemistry',
  441: 'Civil and Environmental Engineering',
  4419: 'Departmemt of Aerospace Engineering',
  4418: 'Departmemt of Mechanical Engineering',
  331: 'Department of Industrial Systems Engineering',
  151: 'Department of Mathematical Sciences',
  3992: 'Division of Future Vehicle',
  4201: 'Economics Program',
  4431: 'Entrepreneurship Program',
  4305: 'Executive MBA',
  4398: 'Finance Executive MBA',
  4303: 'Finance MBA',
  3919: 'Financial Engineering Program',
  4310: 'Financial Engineering Program',
  973: 'General Required',
  3941: 'Global Information &amp; Telecommunication Technology Program',
  4200: 'Graduate Program for Future Strategy',
  3539: 'Graduate School of Culture Technology',
  4144: 'Graduate School of Information Security',
  4438: 'Graduate School of Innovation & Technology Management',
  4549: 'Graduate School of Knowledge Service Engineering',
  3605: 'Graduate School of Medical Science and Engineering',
  3990: 'Graduate School of Science and Technology Policy',
  4422: 'Graduate School of Web Science Technology',
  3799: 'Graduate school of EEWS',
  3692: 'Graduate school of Nanoscience &amp; Technology',
  4493: 'Green Business and Policy Program',
  340: 'Industrial Design',
  4312: 'Information Management Program',
  3723: 'Information and Communications Engineering',
  4306: 'Information and Media MBA',
  3978: 'Intellectual Property Minor Program for Undergradu',
  3920: 'Master of Science Journalism',
  3882: 'Master of intellectual property',
  421: 'Materials Science and Engineering',
  4141: 'Minor Program in Culture Technology',
  3993: 'Minor Program in Science and Technology Policy',
  4425: 'Moon Soul Graduate School of Future Strategy',
  221: 'Nuclear and Quantum Engineering',
  110: 'Physics',
  2410: 'Polymer Science and Engineering Program',
  4182: 'Professional MBA',
  4427: 'Program of Brain and Cognitive Engineering',
  4547: 'School of Business and Technology Management',
  4548: 'School of Business and Technology Management',
  4421: 'School of Computing',
  4423: 'School of Electrical Engineering',
  4424: 'School of Humanities &amp; Social Sciences',
  4301: 'School of Management Engineering',
  4183: 'Social Entrepreneurship MBA',
  3703: 'Software Graduate Program',
  3701: 'Space Exploration Engineering Program',
  4307: 'Techno-MBA',
  3997: 'The Cho Chun Shik Graduate School for Green Transportation',
  3520: 'The Robotics Program',
  4: 'Undergraduate Research Participation',
};

/**
Graph drawing function
*/
const chartStorage = [];

function getLegendOption(property) {
  const w = $('.chart-body').width();
  if (property === 'kaist-department') {
    return {
      borderColor: '#CCD',
      borderWidth: 1,
      itemWidth: w,
      maxHeight: 150,
    };
  } else if (w < 550) {
    return {
      borderColor: '#CCC',
      borderWidth: 1,
      itemWidth: 100,
      maxHeight: 100,
    };
  }
  return {
    layout: 'vertical',
    align: 'right',
    verticalAlign: 'top',
    y: 30,
    borderColor: '#CCC',
    borderWidth: 1,
  };
}

function getColumnBaseOption(property, fData) {
  return {
    chart: {
      type: 'column',
    },
    title: {
      text: property,
    },
    xAxis: {
      categories: fData.xAxis.categories,
    },
    yAxis: {
      min: 0,
      title: {
        text: null,
      },
      stackLabels: {
        enabled: true,
        style: {
          fontWeight: 'bold',
          color: (Highcharts.theme && Highcharts.theme.textColor) || 'gray',
        },
      },
    },
    legend: getLegendOption(property),
    tooltip: {
      headerFormat: '<b>{point.x}</b><br/>',
      pointFormat: '{series.name}: {point.y}',
    },
  };
}

function gettChartOption(property, fData) {
  const baseOption = getColumnBaseOption(property, fData);
  baseOption.plotOptions = {
    column: {
      stacking: 'normal',
    },
  };
  baseOption.series = fData.series;
  return baseOption;
}

function getrChartOption(property, fData) {
  // recent chart only need last data as array
  const baseOption = getColumnBaseOption(property, fData);
  if (property !== 'kaist-department') {
    const categories = baseOption.xAxis.categories;
    baseOption.xAxis.categories = [categories[categories.length - 1]];
    baseOption.series = $.map(fData.series, (v) => {
      v = $.extend({}, v);
      const vData = v.data;
      v.data = [vData[vData.length - 1]];
      return v;
    });
  } else {
    baseOption.chart.type = 'pie';
    baseOption.series = [{
      name: 'department',
      data: $.map(fData.series, (v) => {
        v = $.extend({}, v);
        const vData = v.data;
        return {
          name: v.name,
          y: vData[vData.length - 1],
        };
      }).sort((a, b) => b.y - a.y),
    }];
    baseOption.plotOptions = {
      pie: {
        dataLabels: {
          enabled: false,
        },
      },
    };
    baseOption.tooltip = {
      pointFormat: '<b>{point.percentage:.1f}%</b>',
    };
    delete baseOption.xAxis;
    delete baseOption.yAxis;
  }
  return baseOption;
}

function drawGraph(fData, property) {
  /* professor, employee */
  if (isEmtOfArr(atomicListGlobal, property)) {
    const x = fData.series[0].data.pop();
    property = property.replace('_', '-');
    $(`#${property}-cell`).text(x);
    return 0;
  }

  property = property.replace('_', '-');

  const tChartOption = gettChartOption(property, fData);
  const tChart = Highcharts.chart(`${property}-t-chart`, tChartOption);
  chartStorage.push(tChart);

  const rChartOption = getrChartOption(property, fData);
  const rChart = Highcharts.chart(`${property}-r-chart`, rChartOption);
  chartStorage.push(rChart);

  return 0;
}

function drawGraphKaist(fData, property, property2nd) {
  let propertyClass = [property, property2nd].join('-');
  propertyClass = propertyClass.replace('_', '-');
  drawGraph(fData, propertyClass);
}

function reflowChart() {
  for (let i = 0; i < chartStorage.length; i += 1) {
    const ch = chartStorage[i];
    ch.reflow();
  }
}


/**
Stats object manipulation function
*/

/* Copy object-tree from originalRoot to newRoot.
   If newRoot has already have some number-leaf,
   just add originalRoot's value. */
function sumOrCopy(originalRoot, newRoot) {
  $.each(originalRoot, (k, v) => {
    if (typeof (v) === 'number') {
      newRoot[k] = newRoot[k] + v || v;
      return;
    }
    if (!isKey(newRoot, k)) {
      newRoot[k] = {};
    }
    sumOrCopy(v, newRoot[k]);
  });
  return newRoot;
}

/* Append 'all' as key to stats.
   It is statstics of sum of all services */
function appendDataOfAll(data) {
  const stats = data.stats;
  const statsAll = {
    alias: 'all',
    data: {},
  };
  $.each(stats, (service, sObj) => {
    sumOrCopy(sObj.data, statsAll.data);
  });
  stats.all = statsAll;
}

/**
@param {obj} data - json object from stats api
@returns {array} - array of services
*/
function getServices(data) {
  const stats = data.stats;
  return Object.keys(stats);
}

function getDataOfService(data, sName) {
  if (typeof (sName) === 'undefined') {
    return {};
  }
  return data.stats[sName].data;
}

function getProperties(sData) {
  const dateArr = Object.keys(sData);
  return Object.keys(sData[dateArr[dateArr.length - 1]]);
}

function getPropertiesKaist(sData) {
  const dateArr = Object.keys(sData);
  return Object.keys(sData[dateArr[dateArr.length - 1]].kaist);
}

/**
@param {obj} pAttrObj - apijson.birthYear
- append {year: 0} which api does not contain for spacing
- compatible to preprocessDataKaist
*/
function preprocessDataBirthYear(pAttrObj) {
  const dateArr = Object.keys(pAttrObj);
  const minDate = min(dateArr);
  const maxDate = max(dateArr);
  for (let d = minDate; d <= maxDate; d += 1) {
    if (dateArr.indexOf(d.toString()) === -1) {
      pAttrObj[d] = 0;
    }
  }
  return pAttrObj;
}

/*
@param {obj} pAttrObj
- change department code to name
*/
function preprocessDataDept(pAttrObj) {
  for (const code in pAttrObj) {
    if (isKey(deptData, code)) {
      renameKey(pAttrObj, code, deptData[code]);
    } else {
      renameKey(pAttrObj, code, `uk-${code}`);
    }
  }
}

/**
parsing json.kaist to 2nd-depth
@param {obj} pAttrObj - apijson.kaist
@param {string} property2nd - birthYear, department, employee, gender, professor, startYear
@return preprocessed pAttrObj;
*/
function preprocessDataKaist(pAttrObj, property2nd) {
  const p2ndAttrObj = pAttrObj[property2nd];
  switch (property2nd) {
  case 'birthYear':
    preprocessDataBirthYear(p2ndAttrObj);
    break;
  case 'department':
    preprocessDataDept(p2ndAttrObj);
    break;
  default:
    break;
  }
}

/*
manipulate formattedObj for purpose
- birthYear: append {year: 0} which api does not contain for spacing

@return: rValues
*/
function preprocessData(attrObj, property, property2nd) {
  let pAttrObj = attrObj[property];
  switch (property) {
  case 'account':
    delete pAttrObj.all;
    break;
  case 'birthYear':
    pAttrObj = preprocessDataBirthYear(pAttrObj);
    break;
  case 'kaist':
    pAttrObj = preprocessDataKaist(pAttrObj, property2nd);
    break;
  default:
    break;
  }
}

/*
There's bottle neck at drawing chart which has
many bars. And label of bar need enough space.
So, system should select part of data.

Heuristic methodologically, #bar = (width of chart) / 40

windowSize = Math.ceil(#sData /(#bar - 1))
e.g.) #bar = 4, #sData = 10
windowSize = ceil(10/(4-1)) = 3
0 1 2 3 4 5 6 7 8 9
s   s   s   s
*/
function reduceData(sData, num) {
  const keyArr = Object.keys(sData);
  const windowSize = Math.ceil(keyArr.length / (num - 1));
  for (const idx in keyArr) {
    if (idx % windowSize !== 0) {
      delete sData[keyArr[idx]];
    }
  }
}

/*
@param {obj} sData - Data format
{
  2016-08-17T12:46:56+00:00: {
    account: {
      all: intAll,
      email: intEmail,
      ...
    },
  },
  2016-08-18T12:55:35+00:00: {
    ...
  },
}

@return {obj} - Data format
{
  <property>: {
    series: [
      {
        name: 'label1',
        data: [y1, y2, y3]
      },
      {
        name: 'label2',
        data: [y1, y2, y3]
      }
    ],
    xAxis: {
      categories: ['x1', 'x2', 'x3']
    },
  },
  kaist: {
    2ndProperty: {
      series: [...],
      xAxis: {...}
    },
    department: {
      series: [
        {
          name: <name>,
          y: <y>
        },
      ]
    }
  }
}
*/

function getFormattedData(sData) {
  function simplifyDate(_sData) {
    for (const d in _sData) {
      renameKey(_sData, d, d.split('+')[0]);
    }
  }

  function getDateArr() {
    return Object.keys(sData).sort();
  }

  function buildSpace(dateArr, propertiesArr, propertiesKaistArr) {
    let formattedObj = {};
    let idx;
    for (idx = 0; idx < propertiesArr.length; idx += 1) {
      const p = propertiesArr[idx];
      if (p !== 'kaist') {
        formattedObj = setEmtToObj(formattedObj, [p, 'series'], {});
        formattedObj = setEmtToObj(formattedObj, [p, 'xAxis', 'categories'], dateArr);
      }
    }
    for (idx = 0; idx < propertiesKaistArr.length; idx += 1) {
      const pk = propertiesKaistArr[idx];
      formattedObj = setEmtToObj(formattedObj, ['kaist', pk, 'series'], {});
      formattedObj = setEmtToObj(formattedObj, ['kaist', pk, 'xAxis', 'categories'], dateArr);
    }
    return formattedObj;
  }

  const numOfBar = Math.ceil($('.chart-body').width() / 50);
  simplifyDate(sData);
  reduceData(sData, numOfBar);
  const dateArr = getDateArr();
  const propertiesArr = getProperties(sData);
  const propertiesKaistArr = getPropertiesKaist(sData);
  const formattedObj = buildSpace(dateArr, propertiesArr, propertiesKaistArr);

  for (let idx = 0; idx < dateArr.length; idx += 1) {
    const dateKey = dateArr[idx];
    const attrObj = sData[dateKey];

    for (const property in attrObj) {
      if (property !== 'kaist') {
        preprocessData(attrObj, property);
        for (const label in attrObj[property]) {
          if (!isValidKeyArr(formattedObj, [property, 'series', label])) {
            formattedObj[property].series[label] = {
              name: label,
              data: [],
            };
          }
          formattedObj[property].series[label].data.push(attrObj[property][label]);
        }
      } else { /* kaist case */
        for (const property2nd in attrObj[property]) {
          const attr2ndObj = attrObj[property];

          preprocessData(attrObj, property, property2nd);

          if (isEmtOfArr(atomicListGlobal, `${property}-${property2nd}`)) {
            const atom = attr2ndObj[property2nd];
            attr2ndObj[property2nd] = [atom];
          }

          for (const label in attr2ndObj[property2nd]) {
            if (!isValidKeyArr(formattedObj, [property, property2nd, 'series', label])) {
              formattedObj[property][property2nd].series[label] = {
                name: label,
                data: [],
              };
            }
            formattedObj[property][property2nd].series[label].data
              .push(attrObj[property][property2nd][label]);
          }
        }
      }
    }
  }

  for (const p in formattedObj) {
    if (p !== 'kaist') {
      formattedObj[p].series = makeFormattedToArr(formattedObj[p].series);
    } else {
      for (const pk in formattedObj[p]) {
        formattedObj[p][pk].series = makeFormattedToArr(formattedObj[p][pk].series);
      }
    }
  }
  return formattedObj;
}


/**
DOM manipulation function with jquery
*/
function addServices(services) {
  for (const s of services) {
    if (!s.startsWith('test')) {
      $('#service-dropdown-menu').append(
        `<li id=dropdown-${s} class="dropdown-service"  ><a href="#">${s}</a></li>`,
      );
    }
  }
}

function changeService(sName) {
  $('.s-name').text(sName);
}

function findDropdownMenuPos() {
  const $dmLeft = $('#service-dropdown').position();
  $('#service-dropdown-menu').css('left', $dmLeft.left);
}

function setDateToCalendar(sDate, eDate) {
  $('.s-date').val(sDate);
  $('.e-date').val(eDate);
}

function destroyNotAuthChart(sData) {
  const len = Object.keys(sData).length;
  if (len === 0) {
    $('.chart-lv-1').remove();
    $('.chart-lv-2').remove();
  } else if (len < 3) {
    $('.chart-lv-2').remove();
  }
}


/**
jquery ajax success function
 */
function successStats(data) {
  /* Add up all fields to 'all' key
     when there's more than one service */
  if (Object.keys(data.stats).length > 1) {
    appendDataOfAll(data);
  }

  const serviceList = getServices(data);
  const serviceToShow = serviceList[serviceList.length - 1];
  const sData = getDataOfService(data, serviceToShow);
  changeService(serviceToShow);

  if (Object.keys(sData).length !== 0) {
    const propertyArr = getProperties(sData);
    const propertyKaistArr = getPropertiesKaist(sData);
    const formattedData = getFormattedData(sData);
    for (let idx = 0; idx < propertyArr.length; idx += 1) {
      const property = propertyArr[idx];

      if (property !== 'kaist') {
        const fData = formattedData[property];
        drawGraph(fData, property);
      } else {
        for (const kaidx in propertyKaistArr) {
          const propertyKaist = propertyKaistArr[kaidx];
          const fData = formattedData[property][propertyKaist];
          drawGraphKaist(fData, property, propertyKaist);
        }
      }
    }
  } else if (!firstCallGlobal) {
    alert('선택한 구간의 데이터가 없습니다!');
  }

  /* only first call, add services to dropdown */
  if (firstCallGlobal) {
    addServices(serviceList);
    firstCallGlobal = false;
    destroyNotAuthChart(sData);
  }
}

/**
jquery ajax call
@param - read https://wiki.sparcs.org/w/index.php/SPARCS_SSO_API_%EB%AA%85%EC%84%B8
 */
function getStats(...args) {
  const argNames = ['client_ids', 'date_from', 'date_to'];
  const param = {};
  for (let idx = 0; idx < args.length; idx += 1) {
    param[argNames[idx]] = args[idx];
  }
  $.ajax({
    url: '/api/v2/stats/',
    data: param,
    success: successStats,
    dataType: 'Json',
  });
}


/* Event Handler */
$('.input-daterange').datepicker({
  autoclose: true,
  todayHighlight: true,
  format: 'yyyy-mm-dd',
});

$(document).ready(() => {
  $('.nav-tabs a:first').tab('show');
  setDateToCalendar(sDateGlobal, eDateGlobal);
  getStats(serviceGlobal, sDateGlobal, eDateGlobal);
  findDropdownMenuPos();
});

$(window).resize(() => {
  findDropdownMenuPos();
});

$('body').on('click', '.dropdown-service', (x) => {
  serviceGlobal = x.currentTarget.innerText.trim();
  changeService(serviceGlobal);
});

$('.btn-get-stat').click(() => {
  sDateGlobal = $('.s-date').val();
  eDateGlobal = $('.e-date').val();
  chartStorage.length = 0;
  getStats(serviceGlobal, sDateGlobal, eDateGlobal);
});

$('.nav-tabs').click(() => {
  setTimeout(() => {
    reflowChart();
  }, 0);
});

$(window).resize(() => {
  for (let i = 0; i < chartStorage.length; i += 1) {
    const ch = chartStorage[i];
    if (ch.legend.options.borderColor === '#CCD') {
      ch.legend.update(getLegendOption('kaist-department'));
    }
  }
});
