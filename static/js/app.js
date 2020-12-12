var data = []
var token = ""

jQuery(document).ready(function () {
    var slider = $('#max_words')
    slider.on('change mousemove', function (evt) {
        $('#label_max_words').text('# words in summary: ' + slider.val())
    })

    var slider2 = $('#num_beams')
    slider2.on('change mousemove', function (evt) {
        $('#label_num_beams').text('# beam search: ' + slider2.val())
    })

    $('#btn-process').on('click', function () {
        input_text_name = $('#txt_input_name').val()
        input_text_body = $('#txt_input_body').val()
        // alert("1")
        // alert(input_text_name)
        // alert(input_text_body)
        // alert("2")
        // model = $('#input_model').val()
        // num_words = $('#max_words').val()
        // num_beams = $('#num_beams').val()
        $.ajax({
            url: '/predict',
            type: "post",
            contentType: "application/json",
            dataType: "json",
            data: JSON.stringify({
                "input_text_name": input_text_name,
                "input_text_body": input_text_body
                // "model": model,
                // "num_words": num_words,
                // "num_beams": num_beams
            }),
            beforeSend: function () {
                $('.overlay').show()
            },
            complete: function () {
                $('.overlay').hide()
            }
        }).done(function (jsondata, textStatus, jqXHR) {
            console.log(jsondata)     
            $('#input_summary_document').val(jsondata['response']['summary_document'])
            $('#input_summary_sents').val(jsondata['response']['summary_sents'])
        }).fail(function (jsondata, textStatus, jqXHR) {
            alert(jsondata['responseJSON']['message'])
        });
    })


})