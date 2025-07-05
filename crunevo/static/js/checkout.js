function initCheckoutShipping() {
  const deliveryRadio = document.getElementById('delivery');
  const pickupRadio = document.getElementById('pickup');
  const fields = document.getElementById('shippingFields');
  if (!deliveryRadio || !pickupRadio || !fields) return;

  function toggle() {
    if (deliveryRadio.checked) {
      fields.classList.remove('tw-hidden');
    } else {
      fields.classList.add('tw-hidden');
    }
  }
  deliveryRadio.addEventListener('change', toggle);
  pickupRadio.addEventListener('change', toggle);
  toggle();
}

window.initCheckoutShipping = initCheckoutShipping;
