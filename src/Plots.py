# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 14:32:59 2022

@author: vaska
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def plot_MUF(ltb,lts, Number_of_ln_values, ln_values, energy_values, title='MUF', file_name='MUF.png'):
    lt_b=ltb
    lt_s=lts
    N=Number_of_ln_values
    ln=ln_values
    e=energy_values

    fig, ax = plt.subplots()

    ax.plot(e, ln, '-o', ms=20, alpha=0.7, mfc='orange')
    ##dashed lines for lt_s and lt_b across the whole plot and a red line at zero energy
    ax.axhline(lt_s, linestyle='--', color='k', label='λt_s')
    ax.axhline(lt_b, linestyle='--', color='k', label='΄λt_b')
    ax.axvline(0, linestyle='--', color='r')
    ax.set_title(title)
    ax.set_ylabel('Τιμή της Ενέργειας στην P2P αγορά (€/kWh)')
    ax.set_xlabel('Ενέργεια που Επιθυμεί να Ανταλλάξει ο Prosumer (kWh)')

    ax.grid()
    #fig.figimage(im, 10, 10, zorder=3, alpha=.5)

    fig.savefig(file_name, bbox_inches='tight')
    plt.close(fig)
    
    
def plot_scenarios(loads,realization,Number_of_Scenarios, file_name='scenarios.png'):
    df=pd.DataFrame()
    df=loads
    df['index']=df.index
    W=Number_of_Scenarios
    t = df['index']
    s=realization

    fig, ax = plt.subplots()
    for w in range(W-1):
        ax.plot(t, df['scenario '+str(w)], 'r')  
    ax.plot(t, df['scenario '+str(W-1)], 'r', label='Generated_scenarios') #επιλεγω να βαλω την τελευτααι επαναλυψη χωριστα για να βαλω εκει το label
    ax.plot(t, s, 'b', label='Realization')
    ax.set(xlabel='Time step', ylabel='Load',
    title='Scenarios')
    ax.grid()
    plt.legend(loc='upper left')
    fig.savefig(file_name, bbox_inches='tight')
    plt.close(fig)