function StudentEditBadge(runtime, element) {
    $('.save-button', element).bind('click', function() {
        var data = {
			'bg_id': $('#bg_id_input').val(),
			'debug_mode': $('#debug_mode_input').val(),
			'form_text':$('#form_text_input').val(),
			'congratulations_text':$('#congratulations_text_input').val(),
			'enough_text':$('#enough_text_input').val(),
			'required_score':$('#required_score_input').val(),
			'badge_pro_user':$('#claim_prov_usr_input').val(),
			'badge_pro_pwd':$('#claim_prov_pwd_input').val(),
			'scope_score':$('#scope_score_input').val(),			
		};
        var handlerUrl = runtime.handlerUrl(element, 'studio_save');
        $.post(handlerUrl, JSON.stringify(data)).complete(function() {
            window.location.reload(false);
        });
    });

    $('.cancel-button', element).bind('click', function() {
        runtime.notify('cancel', {});
    });
}
