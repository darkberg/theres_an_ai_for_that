
class user {
	constructor () {
		this.email = null,
		this.password = null,
		this.error_email = null,
		this.error_password = null
	}
}

user_ = new user;

var user_login = new Vue({
	el: "#login",
	mounted: function(event) {

		Vue.prototype.$http = axios;

	},
    created: function () {
        window.addEventListener('keyup', this.keyup)
    },
    destroyed: function () {
        window.removeEventListener('keyup')
    },

	data: {
		user: user_
	},

	methods: {
		user_login_function: function(event) {
			
			console.log("Logging in")
			this.$http.post('/user/login', {
				user: this.user
			})
			.then(function (response) {

			user_login.user.password = null;
			
			console.log(response);
			user_login.user.error_email = response.data['error_email'];
            user_login.user.error_password = response.data['error_password'];

            if (response.data['success'] == true) {
                window.location.href = '/a';
            }

			})
			.catch(function (error) {
			console.log(error);
			});
        },
        keyup: function (event) {

            if (event.keyCode === 13) {  // enter
                this.user_login_function();
            }

        }
	}
})