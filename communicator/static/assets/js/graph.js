function random_rgba() {
  var o = Math.round, r = Math.random, s = 255;
  return 'rgba(' + o(r()*s) + ',' + o(r()*s) + ',' + o(r()*s) + ',' + r().toFixed(1) + ')';
}

function dict2datasets(data) {
  var datasets = [];
  Object.keys(data).forEach(function (key) {
    datasets.push(
      {
        label: key,
        fill: true,
        backgroundColor: random_rgba(),
        borderCapStyle: 'butt',
        data: data[key],
      })
  });
  return datasets;
}