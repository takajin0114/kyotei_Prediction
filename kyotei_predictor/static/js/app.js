

$(document).ready(function() {
    // レースデータの取得と表示
    function fetchRaceData() {
        $.get('/api/race_data', function(data) {
            if (data && data.race_entries) {
                let html = '<table class="table table-bordered race-table">';
                html += '<thead><tr><th>艇番</th><th>選手名</th><th>級別</th><th>全国勝率</th><th>当地勝率</th><th>ボート</th><th>モーター</th></tr></thead>';
                html += '<tbody>';

                data.race_entries.forEach(entry => {
                    html += `<tr class="${entry.current_rating}">
                        <td>${entry.pit_number}</td>
                        <td>${entry.last_name} ${entry.first_name}</td>
                        <td>${entry.current_rating}</td>
                        <td>${entry.rate_in_all_stadium.toFixed(2)}</td>
                        <td>${entry.rate_in_event_going_stadium.toFixed(2)}</td>
                        <td>${entry.boat_number} (${entry.boat_quinella_rate.toFixed(1)}%)</td>
                        <td>${entry.motor_number} (${entry.motor_quinella_rate.toFixed(1)}%)</td>
                    </tr>`;
                });

                html += '</tbody></table>';
                $('#race-data').html(html);
            } else {
                $('#race-data').html('<p class="text-center">レースデータが取得できませんでした</p>');
            }
        }).fail(function() {
            $('#race-data').html('<p class="text-center text-danger">レースデータの取得に失敗しました</p>');
        });
    }

    // 予測ボタンのクリックイベント
    $('#predict-btn').click(function() {
        $(this).prop('disabled', true);
        $(this).html('<i class="fas fa-spinner fa-spin"></i> 予測中...');

        // レースデータを取得
        $.get('/api/race_data', function(raceData) {
            // 予測APIを呼び出し
            $.post('/api/predict', JSON.stringify({
                race_entries: raceData.race_entries
            }), function(prediction) {
                let output = '<div class="prediction-result prediction-success">';
                output += '<h3>予測結果</h3>';
                output += `<p><strong>予想1着:</strong> ${prediction.predicted_winner.pit_number}号艇 ${prediction.predicted_winner.last_name} ${prediction.predicted_winner.first_name}</p>`;
                output += `<p><strong>勝率:</strong> ${prediction.predicted_winner.rate_in_all_stadium.toFixed(2)}</p>`;
                output += `<p><strong>信頼度:</strong> ${(prediction.confidence * 100).toFixed(1)}%</p>`;
                output += '</div>';

                $('#prediction-output').html(output);
            }).fail(function() {
                $('#prediction-output').html('<div class="prediction-result prediction-error"><p class="text-danger">予測の実行に失敗しました</p></div>');
            }).always(function() {
                $('#predict-btn').prop('disabled', false);
                $('#predict-btn').html('<i class="fas fa-magic"></i> 予測を実行');
            });
        }).fail(function() {
            $('#prediction-output').html('<div class="prediction-result prediction-error"><p class="text-danger">レースデータの取得に失敗しました</p></div>');
            $('#predict-btn').prop('disabled', false);
            $('#predict-btn').html('<i class="fas fa-magic"></i> 予測を実行');
        });
    });

    // ページ読み込み時にレースデータを取得
    fetchRaceData();
});

