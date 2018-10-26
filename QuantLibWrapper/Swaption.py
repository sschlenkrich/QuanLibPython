#!/usr/bin/python

import pandas
import QuantLib as ql

class Swaption:

    # Python constructor
    def __init__(self, underlyingSwap, expiryDate, normalVolatility):
        self.underlyingSwap = underlyingSwap
        self.exercise = ql.EuropeanExercise(expiryDate)
        self.swaption = ql.Swaption(self.underlyingSwap.swap,self.exercise,ql.Settlement.Physical)
        volQuote = ql.SimpleQuote(normalVolatility)
        volHandle = ql.QuoteHandle(volQuote)
        initialEngine = ql.BachelierSwaptionEngine(self.underlyingSwap.discHandle,volHandle,ql.Actual365Fixed())
        self.swaption.setPricingEngine(initialEngine)

    def npv(self):
        return self.swaption.NPV()

    def annuity(self):
        return self.underlyingSwap.annuity()

    def bondOptionDetails(self):
        # calculate expiryTime, payTimes, cashFlows, strike and
        # c/p flag as inputs to Hull White analytic formula
        result = {}
        result['callOrPut'] = 1.0 if self.underlyingSwap.payerOrReceiver==ql.VanillaSwap.Receiver else -1.0
        result['strike']    = 0.0
        refDate  = self.underlyingSwap.discHandle.referenceDate()
        result['expiryTime'] = ql.Actual365Fixed().yearFraction(refDate,self.exercise.dates()[0])
        fixedLeg = [ [ ql.Actual365Fixed().yearFraction(refDate,cf.date()), cf.amount() ]
                     for cf in self.underlyingSwap.swap.fixedLeg() ]
        result['fixedLeg'] = fixedLeg
        floatLeg = [ [ ql.Actual365Fixed().yearFraction(refDate,ql.as_coupon(cf).accrualStartDate()),
                       ((1 + ql.as_coupon(cf).accrualPeriod()*ql.as_coupon(cf).rate()) *
                        self.underlyingSwap.discHandle.discount(ql.as_coupon(cf).accrualEndDate()) /
                        self.underlyingSwap.discHandle.discount(ql.as_coupon(cf).accrualStartDate()) - 1.0) *
                       ql.as_coupon(cf).nominal() 
                       ] 
                     for cf in self.underlyingSwap.swap.floatingLeg() ]
        result['floatLeg'] = floatLeg    
        payTimes = [ floatLeg[0][0]  ]          +       \
                   [ cf[0] for cf in floatLeg ] +       \
                   [ cf[0] for cf in fixedLeg ] +       \
                   [ ql.Actual365Fixed().yearFraction(refDate,ql.as_coupon(
                     self.underlyingSwap.swap.floatingLeg()[-1]).accrualEndDate()) ]
        caschflows = [ -ql.as_coupon(self.underlyingSwap.swap.floatingLeg()[0]).nominal() ] +  \
                     [ -cf[1] for cf in floatLeg ] +    \
                     [  cf[1] for cf in fixedLeg ] +    \
                     [ ql.as_coupon(self.underlyingSwap.swap.floatingLeg()[0]).nominal() ]
        result['payTimes'  ] = payTimes
        result['caschflows'] = caschflows        
        return result