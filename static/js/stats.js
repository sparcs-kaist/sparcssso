/* department data */
const deptData = {
  0: 'Undecided',
  4: 'Undergraduate Research Participation',
  33: 'Capstone Design',
  110: 'Physics',
  132: 'Biological Sciences',
  150: 'Chemistry',
  151: 'Department of Mathematical Sciences',
  221: 'Nuclear and Quantum Engineering',
  331: 'Department of Industrial Systems Engineering',
  340: 'Industrial Design',
  421: 'Materials Science and Engineering',
  441: 'Civil and Environmental Engineering',
  451: 'Chemical and Biomolecular Engineering',
  936: 'Business',
  973: 'General Required',
  2222: 'Biomedical Science and Engineering Program',
  2410: 'Polymer Science and Engineering Program',
  3520: 'The Robotics Program',
  3539: 'Graduate School of Culture Technology',
  3605: 'Graduate School of Medical Science and Engineering',
  3648: 'Bio and Brain Engineering',
  3692: 'Graduate school of Nanoscience &amp; Technology',
  3701: 'Space Exploration Engineering Program',
  3703: 'Software Graduate Program',
  3723: 'Information and Communications Engineering',
  3799: 'Graduate school of EEWS',
  3882: 'Master of intellectual property',
  3919: 'Financial Engineering Program',
  3920: 'Master of Science Journalism',
  3941: 'Global Information &amp; Telecommunication Technology Program',
  3978: 'Intellectual Property Minor Program for Undergradu',
  3990: 'Graduate School of Science and Technology Policy',
  3992: 'Division of Future Vehicle',
  3993: 'Minor Program in Science and Technology Policy',
  3997: 'The Cho Chun Shik Graduate School for Green Transportation',
  4141: 'Minor Program in Culture Technology',
  4144: 'Graduate School of Information Security',
  4182: 'Professional MBA',
  4183: 'Social Entrepreneurship MBA',
  4200: 'Graduate Program for Future Strategy',
  4201: 'Economics Program',
  4301: 'School of Management Engineering',
  4303: 'Finance MBA',
  4305: 'Executive MBA',
  4306: 'Information and Media MBA',
  4307: 'Techno-MBA',
  4310: 'Financial Engineering Program',
  4312: 'Information Management Program',
  4398: 'Finance Executive MBA',
  4418: 'Departmemt of Mechanical Engineering',
  4419: 'Departmemt of Aerospace Engineering',
  4421: 'School of Computing',
  4422: 'Graduate School of Web Science Technology',
  4423: 'School of Electrical Engineering',
  4424: 'School of Humanities &amp; Social Sciences',
  4425: 'Moon Soul Graduate School of Future Strategy',
  4427: 'Program of Brain and Cognitive Engineering',
  4431: 'Entrepreneurship Program',
  4438: 'Graduate School of Innovation & Technology Management',
  4493: 'Green Business and Policy Program',
  4547: 'School of Business and Technology Management',
  4548: 'School of Business and Technology Management',
  4549: 'Graduate School of Knowledge Service Engineering',
};

const getExtreme = (list, compare) => {
  if (!list) {
    return undefined;
  }
  let m;
  list.forEach((item) => {
    if (m === undefined || compare(m, item)) {
      m = item;
    }
  });
  return m;
};
const getMin = list => getExtreme(list, (x, y) => x > y);
const getMax = list => getExtreme(list, (x, y) => x < y);
const getMinMax = list => [getMin(list), getMax(list)];
const toInt = list => list.map(x => parseInt(x, 10));
const range = (a, b) => Array.from({ length: (b - a) + 1 }, (x, i) => i + a);

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
  title: {
    text: title,
  },
  tooltip: {
    headerFormat: '{point.key}: ',
    pointFormat: '<b>{point.y}</b>',
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
});

const renderRecentAccount = () => {
  const accountStat = recentStat.account;
  ['all', 'email', 'fb', 'tw', 'kaist', 'test'].forEach((type) => {
    $(`#account-${type}-r`).text(accountStat[type]);
  });
};

const renderRecentKAISTMember = () => {
  const kaistStat = recentStat.kaist;
  ['professor', 'employee'].forEach((type) => {
    $(`#member-${type}-r`).text(kaistStat[type]);
  });
};

const renderRecentGender = () => {
  const kaistStat = recentStat.kaist;
  const genderStat = recentStat.gender;
  const genderKStat = kaistStat ? kaistStat.gender : {};
  const genders = ['female', 'male', 'etc', 'hide'];
  const [seriesDataLocal, seriesDataKAIST] = [genderStat, genderKStat].map(
    list => genders.map(gender => list[gender] || 0),
  );

  Highcharts.chart('gender-r-chart', getRecentChartOptions({
    type: 'column',
    title: 'Gender',
    categories: genders,
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
  const [minYear, maxYear] = toInt(getMinMax([
    ...Object.keys(birthStat),
    ...Object.keys(birthKStat),
  ]));
  const years = range(minYear, maxYear);
  const [seriesDataLocal, seriesDataKAIST] = [birthStat, birthKStat].map(
    list => years.map(year => list[year] || 0),
  );

  Highcharts.chart('birth-r-chart', getRecentChartOptions({
    type: 'column',
    title: 'Birth Year',
    categories: years,
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
  const [minYear, maxYear] = toInt(getMinMax(Object.keys(classOfStat)));
  const years = range(minYear, maxYear);
  const seriesData = years.map(year => classOfStat[year] || 0);

  Highcharts.chart('class-of-r-chart', getRecentChartOptions({
    type: 'column',
    title: 'Class Of',
    yAxisTitle: 'Number of Users',
    categories: years,
    series: [{
      name: 'default',
      data: seriesData,
      showInLegend: false,
    }],
  }));
};

const renderRecentDept = () => {
  const deptStat = recentStat.kaist.department;
  const deptIds = Object.keys(deptStat);
  const seriesData = deptIds.map(deptId => ({
    name: deptData[deptId] || `Unknown ${deptId}`,
    y: deptStat[deptId],
    showInLegend: false,
  }));

  Highcharts.chart('dept-r-chart', getRecentChartOptions({
    type: 'pie',
    title: 'Department',
    categories: deptIds,
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
  stacking,
}) => ({
  chart: {
    zoomType: 'x',
  },
  legend: {
    enabled: series.length < 10,
  },
  plotOptions: {
    area: {
      stacking: stacking === false ? undefined : 'normal',
    },
  },
  series,
  title: {
    text: title,
  },
  tooltip: {
    xDateFormat: '%Y-%m-%d',
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
});

const renderTotalStats = () => {
  const transformToDateValue = (valueFunc) => {
    const dates = Object.keys(allStats).sort();
    const results = dates.map(date => (
      [moment(date).unix() * 1000, valueFunc(allStats[date])]
    ));
    return results;
  };

  const chartMap = [{
    html: 'account-t-chart',
    title: 'Account Type',
    types: () => Object.keys(recentStat.account),
    valueFunc: t => s => s.account[t],
    stacking: false,
  }, {
    html: 'gender-t-chart',
    title: 'Gender',
    types: () => Object.keys(recentStat.gender),
    valueFunc: t => s => s.gender[t],
    level: 1,
  }, {
    html: 'birth-t-chart',
    title: 'Birth Year',
    types: () => Object.keys(recentStat.birth_year),
    valueFunc: t => s => s.birth_year[t],
    level: 1,
  }, {
    html: 'kaist-gender-t-chart',
    title: 'Gender (KAIST)',
    types: () => Object.keys(recentStat.kaist.gender),
    valueFunc: t => s => s.kaist.gender[t],
    level: 2,
  }, {
    html: 'kaist-birth-t-chart',
    title: 'Birth Year (KAIST)',
    types: () => Object.keys(recentStat.kaist.birth_year),
    valueFunc: t => s => s.kaist.birth_year[t],
    level: 2,
  }, {
    html: 'dept-t-chart',
    title: 'Department',
    types: () => Object.keys(recentStat.kaist.department),
    nameFunc: k => deptData[k] || `Unknown ${k}`,
    valueFunc: t => s => s.kaist.department[t],
    level: 2,
  }, {
    html: 'class-of-t-chart',
    title: 'Class Of',
    types: () => Object.keys(recentStat.kaist.start_year),
    valueFunc: t => s => s.kaist.start_year[t],
    level: 2,
  }, {
    html: 'kaist-member-t-chart',
    title: 'Professor / Employee',
    types: () => ['professor', 'employee'],
    valueFunc: t => s => s.kaist[t],
    level: 2,
  }];

  chartMap.forEach((chart) => {
    if ((chart.level || 0) > level) {
      return;
    }
    const series = chart.types().map(type => ({
      type: 'area',
      name: chart.nameFunc ? chart.nameFunc(type) : type,
      data: transformToDateValue(chart.valueFunc(type)),
    }));
    Highcharts.chart(chart.html, getTotalChartOptions({
      title: chart.title,
      series,
      stacking: chart.stacking,
    }));
  });
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
  serviceIdList.forEach((serviceId) => {
    const serviceName = serviceList[serviceId];
    $('#service-list').append(
      `<li class="dropdown-service"><a href="#" data-id="${serviceId}">${serviceName}</a></li>`,
    );
  });

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
