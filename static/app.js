window.addEventListener('DOMContentLoaded', function () {
	const allMessages = document.querySelectorAll('.message');

	//prettier-ignore
	for (let message of allMessages) {
		message.addEventListener('click', async function (e) {
			e.preventDefault();
            console.dir(e)
            if(e.target.nodeName==='BUTTON' || e.target.nodeName==='I'){
            console.log(e.target.nodeName)
            console.log(e.target)
            const route = e.target.dataset.likePostRoute;
			await fetch(`${route}`, {
				method: 'POST'
			});
            document.querySelector(`[data-like-post-route="${route}"]`).classList.toggle('thumbs-up-on')
            document.querySelector(`[data-like-post-route="${route}"]`).classList.toggle('btn-secondary')
        }
        else if(e.target.classList.contains('timeline-image') || e.target.classList.contains('at-sign')){
            const href = e.target.parentElement.href
            if(href === undefined){
                window.location.href = e.target.href;
            }
            else {
                window.location.href = href;
            }
        }
        else if(e.target.nodeName !== 'LI'){
            window.location.href = e.target.parentElement.dataset.messageRoute
        }
        else {
            window.location.href = e.target.dataset.messageRoute;
        }
		});
	}
});
