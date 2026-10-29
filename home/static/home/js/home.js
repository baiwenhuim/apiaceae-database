$(function () {
  request({
    url: 'statistics/general-data',
    successCallback: function (data) {
      $('.monomer').text(data.complexity['monomer']);
      $('.multimer').text(data.complexity['multimer']);
      $('.multi_peptide').text(data.complexity['multi_peptide']);
      $('.peptide_with_synergy').text(data.peptideCountWithSynergy);
    }
  });
})