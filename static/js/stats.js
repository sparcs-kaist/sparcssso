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

const getExtreme = (list, compare) => {
  if (!list) {
    return undefined;
  }
  let m;
  for (const item of list) {
    if (m === undefined || compare(m, item)) {
      m = item;
    }
  }
  return m;
};
const getMin = list => getExtreme(list, (x, y) => x > y);
const getMax = list => getExtreme(list, (x, y) => x < y);

const toISODate = x => x.format('YYYY-MM-DD');
const today = toISODate(moment());
let startDate = toISODate(moment().subtract(90, 'days'));
let endDate = today;
let selectedServiceId = 'all';

let level = 0;
const serviceList = {};
let allStats;
let recentStat;

const getRecentChartOptions = ({
  type,
  title,
  categories,
  series,
}) => ({
  chart: {
    type,
  },
  title: {
    text: title,
  },
  xAxis: {
    categories,
  },
  yAxis: {
    min: 0,
    title: {
      text: 'Number of Users',
    },
  },
  tooltip: {
    headerFormat: '{point.key}: ',
    pointFormat: '<b>{point.y}</b>',
  },
  plotOptions: {
    pie: {
      allowPointSelect: true,
      cursor: 'pointer',
      dataLabels: {
        enabled: false,
      },
    },
  },
  series,
});

const renderRecentAccount = () => {
  const accountStat = recentStat.account;
  const types = ['all', 'email', 'fb', 'tw', 'kaist', 'test'];
  for (const type of types) {
    $(`#account-${type}-r`).text(accountStat[type]);
  }
};

const renderRecentKAISTMember = () => {
  const kaistStat = recentStat.kaist;
  for (const type of ['employee', 'professor']) {
    $(`#member-${type}-r`).text(kaistStat[type]);
  }
};

const renderRecentGender = () => {
  const kaistStat = recentStat.kaist;
  const genderStat = recentStat.gender;
  const genderKStat = kaistStat ? kaistStat.gender : {};
  const categories = ['female', 'male', 'etc', 'hide'];
  const seriesDataLocal = [];
  const seriesDataKAIST = [];

  for (const type of categories) {
    seriesDataLocal.push(genderStat[type] || 0);
    seriesDataKAIST.push(genderKStat[type] || 0);
  }

  Highcharts.chart('gender-r-chart', getRecentChartOptions({
    type: 'column',
    title: 'Gender',
    categories,
    series: [{
      name: 'local',
      data: seriesDataLocal,
      showInLegend: !!kaistStat,
    }, {
      name: 'kaist',
      data: seriesDataKAIST,
      showInLegend: !!kaistStat,
    }],
  }));
};

const renderRecentBirth = () => {
  const kaistStat = recentStat.kaist;
  const birthStat = recentStat.birth_year;
  const birthKStat = kaistStat ? kaistStat.birth_year : {};

  const getExtremeYear = f => parseInt(f([
    f(Object.keys(birthStat)),
    f(Object.keys(birthKStat)),
  ]), 10);
  const minYear = getExtremeYear(getMin);
  const maxYear = getExtremeYear(getMax);
  const categories = [];
  const seriesDataLocal = [];
  const seriesDataKAIST = [];
  for (let year = minYear; year <= maxYear; year += 1) {
    categories.push(year);
    seriesDataLocal.push(birthStat[year] || 0);
    seriesDataKAIST.push(birthKStat[year] || 0);
  }

  Highcharts.chart('birth-r-chart', getRecentChartOptions({
    type: 'column',
    title: 'Birth Year',
    categories,
    series: [{
      name: 'local',
      data: seriesDataLocal,
      showInLegend: !!kaistStat,
    }, {
      name: 'kaist',
      data: seriesDataKAIST,
      showInLegend: !!kaistStat,
    }],
  }));
};

const renderRecentClassOf = () => {
  const classOfStat = recentStat.kaist.start_year;

  const minYear = parseInt(getMin(Object.keys(classOfStat)), 10);
  const maxYear = parseInt(getMax(Object.keys(classOfStat)), 10);
  const categories = [];
  const seriesData = [];
  for (let year = minYear; year <= maxYear; year += 1) {
    categories.push(year);
    seriesData.push(classOfStat[year] || 0);
  }

  Highcharts.chart('class-of-r-chart', getRecentChartOptions({
    type: 'column',
    title: 'Class Of',
    yAxisTitle: 'Number of Users',
    categories,
    series: [{
      name: 'default',
      data: seriesData,
      showInLegend: false,
    }],
  }));
};

const renderRecentDept = () => {
  const deptStat = recentStat.kaist.department;

  const categories = Object.keys(deptStat);
  const seriesData = [];
  for (const deptId of categories) {
    const deptName = deptData[deptId] || `Unknown ${deptId}`;
    seriesData.push({
      name: deptName,
      y: deptStat[deptId],
      showInLegend: false,
    });
  }

  Highcharts.chart('dept-r-chart', getRecentChartOptions({
    type: 'pie',
    title: 'Department',
    categories,
    series: [{
      name: 'default',
      data: seriesData,
    }],
  }));
};

const renderRecentStats = () => {
  renderRecentAccount();
  if (level >= 1) {
    renderRecentGender();
    renderRecentBirth();
  }
  if (level >= 2) {
    renderRecentKAISTMember();
    renderRecentClassOf();
    renderRecentDept();
  }
};

const getTotalChartOptions = ({
  title,
  series,
}) => ({
  chart: {
    zoomType: 'x',
  },
  title: {
    text: title,
  },
  xAxis: {
    type: 'datetime',
    dateTimeLabelFormats: {
      day: '%Y-%m-%d',
      week: '%Y-%m-%d',
      month: '%Y-%m',
      year: '%Y',
    },
  },
  yAxis: {
    title: {
      text: 'Number of Users',
    },
  },
  legend: {
    enabled: (series.length < 10),
  },
  tooltip: {
    xDateFormat: '%Y-%m-%d',
  },
  plotOptions: {
    area: {
      stacking: 'normal',
    },
  },
  series,
});

const renderTotalStats = () => {
  const transformToDateValue = (valueFunc) => {
    const results = [];
    const dates = Object.keys(allStats).sort();
    for (const date of dates) {
      results.push([moment(date).unix() * 1000, valueFunc(allStats[date])]);
    }
    return results;
  };

  const chartMap = [{
    html: 'account-t-chart',
    title: 'Account Type',
    types: Object.keys(recentStat.account),
    valueFunc: t => s => s.account[t],
  }, {
    html: 'gender-t-chart',
    title: 'Gender',
    types: Object.keys(recentStat.gender),
    valueFunc: t => s => s.gender[t],
  }, {
    html: 'birth-t-chart',
    title: 'Birth Year',
    types: Object.keys(recentStat.birth_year),
    valueFunc: t => s => s.birth_year[t],
  }, {
    html: 'kaist-gender-t-chart',
    title: 'Gender (KAIST)',
    types: Object.keys(recentStat.kaist.gender),
    valueFunc: t => s => s.kaist.gender[t],
  }, {
    html: 'kaist-birth-t-chart',
    title: 'Birth Year (KAIST)',
    types: Object.keys(recentStat.kaist.birth_year),
    valueFunc: t => s => s.kaist.birth_year[t],
  }, {
    html: 'dept-t-chart',
    title: 'Department',
    types: Object.keys(recentStat.kaist.department),
    nameFunc: k => deptData[k] || `Unknown ${k}`,
    valueFunc: t => s => s.kaist.department[t],
  }, {
    html: 'class-of-t-chart',
    title: 'Class Of',
    types: Object.keys(recentStat.kaist.start_year),
    valueFunc: t => s => s.kaist.start_year[t],
  }, {
    html: 'kaist-member-t-chart',
    title: 'Professor / Employee',
    types: ['professor', 'employee'],
    valueFunc: t => s => s.kaist[t],
  }];

  for (const chart of chartMap) {
    const series = [];
    for (const type of chart.types) {
      series.push({
        type: 'area',
        name: chart.nameFunc ? chart.nameFunc(type) : type,
        data: transformToDateValue(chart.valueFunc(type)),
      });
    }
    Highcharts.chart(chart.html, getTotalChartOptions({
      title: chart.title,
      series,
    }));
  }
};

const renderStats = () => {
  $('#service-name').text(serviceList[selectedServiceId]);
  renderRecentStats();
  renderTotalStats();
};

const resetServiceList = () => {
  const rawIdList = Object.keys(serviceList);
  const serviceIdList = [
    'all',
    ...rawIdList.filter(x => !x.startsWith('sparcs') && x !== 'all').sort(),
    ...rawIdList.filter(x => x.startsWith('sparcs')).sort(),
  ];
  for (const serviceId of serviceIdList) {
    const serviceName = serviceList[serviceId];
    $('#service-list').append(
      `<li class="dropdown-service"><a href="#" data-id="${serviceId}">${serviceName}</a></li>`,
    );
  }

  $('#service-list a').click((e) => {
    const newSelectedId = $(e.target).data('id');
    if (selectedServiceId === newSelectedId) {
      return;
    }
    selectedServiceId = newSelectedId;
    renderStats();
  });

  if (!serviceIdList.includes(selectedServiceId)) {
    selectedServiceId = 'all';
  }
};

const killForbidStats = () => {
  if (level < 1) {
    $('.lv-1').hide();
  }
  if (level < 2) {
    $('.lv-2').hide();
  }
};

const fetchStats = () => (
  $.getJSON('/api/v2/stats/', {
    date_from: startDate,
    date_to: endDate,
  }).done((result) => {
    level = result.level;

    const getLastStat = (stats) => {
      const maxDate = getMax(Object.keys(stats));
      return maxDate ? stats[maxDate] : undefined;
    };
    Object.keys(result.stats).forEach((k) => {
      serviceList[k] = result.stats[k].alias;
    });
    allStats = result.stats[selectedServiceId].data;
    recentStat = getLastStat(allStats);
    resetServiceList();
    killForbidStats();
    renderStats();
  })
);

$(() => {
  $('.date-range').daterangepicker({
    linkedCalendars: false,
    startDate,
    endDate,
    maxDate: today,
    locale: {
      format: 'YYYY-MM-DD',
    },
  }, (start, end) => {
    $('.date-range span').html(`${start} ~ ${end}`);
  });

  $('.date-range').on('apply.daterangepicker', (ev, picker) => {
    startDate = picker.startDate.format('YYYY-MM-DD');
    endDate = picker.endDate.format('YYYY-MM-DD');
    fetchStats();
  });

  fetchStats();
});
